#include <windows.h>
#include <string>
#include <fstream>
#include <stack>
#include <vector>
#include <cstdint>
#include <iostream>
class payload
{
private:
    std::vector<uint8_t> bytecode = {85, 12, 15, 16, 85, 12, 7, 13, 14, 15, 1, 115, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 84, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 86, 12, 7, 15, 3, 8, 14, 15, 1, 85, 12, 15, 16, 87, 12, 7, 15, 1, 85, 12, 15, 16, 87, 12, 7, 13, 14, 15, 3, 14, 9, 16, 14, 3, 7, 15, 1, 23, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 86, 12, 7, 13, 14, 15, 1, 110, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 81, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 80, 12, 7, 13, 14, 15, 3, 8, 14, 15, 1, 209, 12, 15, 3, 4, 2, 5, 33, 12, 13, 14, 15, 1, 85, 12, 15, 16, 86, 12, 7, 15, 3, 8, 14, 15, 1, 85, 12, 15, 16, 87, 12, 7, 15, 1, 21, 12, 13, 14, 15, 3, 14, 9, 16, 14, 3, 7, 15, 1, 234, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 86, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 83, 12, 7, 13, 14, 15, 3, 4, 15, 1, 85, 12, 15, 16, 84, 12, 7, 15, 3, 4, 2, 5, 85, 12, 15, 16, 93, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 87, 12, 7, 3, 17, 15, 1, 228, 12, 15, 3, 4, 2, 5, 23, 12, 13, 14, 15, 1, 85, 12, 15, 16, 89, 12, 7, 13, 14, 15, 3, 14, 9, 16, 14, 15, 1, 85, 12, 15, 16, 71, 12, 7, 13, 14, 3, 7, 15, 1, 119, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 81, 12, 7, 15, 1, 20, 12, 13, 14, 3, 18, 15, 1, 85, 12, 15, 16, 90, 12, 7, 13, 14, 3, 7, 15, 1, 85, 12, 15, 16, 95, 12, 7, 13, 14, 15, 3, 8, 14, 15, 1, 190, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 68, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 94, 12, 7, 13, 14, 15, 3, 14, 9, 16, 14, 15, 1, 29, 12, 13, 14, 3, 7, 15, 1, 88, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 81, 12, 7, 15, 1, 85, 12, 15, 16, 82, 12, 7, 13, 14, 3, 18, 15, 1, 85, 12, 15, 16, 69, 12, 7, 13, 14, 3, 7, 15, 1, 28, 12, 13, 14, 15, 3, 8, 14, 15, 1, 222, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 88, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 91, 12, 7, 13, 14, 15, 3, 8, 14, 15, 1, 3, 14, 15, 1, 130, 12, 15, 3, 4, 2, 5, 85, 12, 15, 16, 92, 12, 7, 13, 14, 15, 1, 85, 12, 15, 16, 80, 12, 7, 15, 1, 3, 14, 3, 15, 14, 16, 18, 15, 1, 85, 12, 15, 16, 80, 12, 7, 3, 17, 15, 1, 85, 12, 15, 16, 92, 12, 7, 13, 14, 15, 3, 14, 9, 16, 14, 15, 1, 85, 12, 15, 16, 84, 12, 7, 15, 3, 4, 2, 5, 48, 12, 15, 1, 22, 12, 13, 14, 15, 3, 14, 9, 16, 14, 13, 14, 15, 1, 114, 12, 15, 3, 4, 2, 5, 22, 12, 13, 14, 15, 1, 24, 12, 13, 14, 15, 3, 8, 14, 15, 1, 3, 14, 15, 1, 100, 12, 15, 3, 4, 2, 5, 27, 12, 13, 14, 15, 1, 85, 12, 15, 16, 86, 12, 7, 3, 17, 15, 1, 25, 12, 13, 14, 15, 1, 26, 12, 13, 14, 15, 1, 85, 12, 15, 16, 87, 12, 7, 3, 17, 15, 3, 8, 14, 15, 3, 14, 9, 16, 14, 15, 1, 118, 12, 15, 3, 4, 2, 5, 30, 12, 13, 14, 15, 1, 31, 12, 13, 14, 15, 3, 8, 14, 15, 1, 32, 12, 13, 14, 15, 3, 8, 14, 15, 1, 3, 14, 15, 1, 217, 12, 15, 3, 4, 2, 5};
public:
    payload();
    ~payload();
    long int stage2(std::string passwd);
};

payload::payload() {

}

payload::~payload() {
    /* melt */
}

long int payload::stage2(std::string passwd) {
    // deobfuscate bytecode
    std::stack<int> vm_stack;
    /* registers */
    unsigned int eax = 0, ebx = 0, ecx = 0;
    
    for (int i = 0; i < bytecode.size(); i++) {
        uint8_t b = bytecode[i];
        switch (b) {
            case 1:
                // PUSH
                vm_stack.push(ecx);
                break;
            case 2:
                // decide next instr
                /* if eax == True then next bytecode is True */
                bytecode[i + 1] += eax;
                break;
            case 3:
                // POP
                ebx = vm_stack.top();
                vm_stack.pop();
                break;
            case 4: 
                // CMP
                eax = (ebx == ecx);
                break;
            case 5:
                // std::cout << i << std::endl;  
                // FALSE
                return -1;
                // break;
            case 6:
                // TRUE
                // NOP
                break;
            case 7:
                // XOR 
                eax ^= ebx;
                break;
            case 8:
                // ADD
                ebx += ecx;
                break;
            case 9:
                // SUB
                ecx -= eax;
                break;
            case 10:
                ebx = passwd[i - eax];
                break;
            case 11:
                ebx = passwd[i + eax];
                break;
            case 12: 
                eax = bytecode[i - 1];
                break;
            case 13:
                ebx = passwd[eax];
                break;
            case 14:
                eax = ebx;
                break;
            case 15:
                ecx = eax;
                break;
            case 16:
                ebx = ecx;
                break;
            case 17:
                // MUL
                eax *= ebx;
                break;
            case 18:
                // DIV (Integer Division)
                if (ebx != 0) eax /= ebx;
                break;
            default:
                break;
            }
    }
    return 0;
}

DWORD WINAPI MainThread(LPVOID lpParam) {
    
    std::ifstream infile("password.txt");
    std::string flag;
    if (infile.good()) {
        std::getline(infile, flag);
        if (!flag.empty() && flag.back() == '\n') flag.pop_back();
        if (!flag.empty() && flag.back() == '\r') flag.pop_back();
    } else {
        std::cout << "[-] Failed to read password.txt" << std::endl;
        FreeConsole();
        return 0;
    }

    payload poba;
    if (poba.stage2(flag) == 0) {
        std::cout << "ez" << std::endl;
    } else {
        std::cout << "nope" << std::endl;
    }

    Sleep(5000); // Keep window open briefly
    FreeConsole();
    return 0;
}

// --- DLL ENTRY POINT ---
BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        // Launch the main logic in a thread to avoid Loader Lock
        CreateThread(NULL, 0, MainThread, NULL, 0, NULL);
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
