#include <windows.h>
#include <winternl.h>
#include <intrin.h>
#include <iostream>
#include <string>
#include "expected_pixels.h"

// output from calc.py
#define HASH_LOADLIBRARYA         0x5FBFF0FB
#define HASH_CREATECOMPATIBLEDC   0xA05CBAE0
#define HASH_CREATEDIBSECTION     0xFFF5B73D
#define HASH_CREATEFONTA          0xEB9A1AB1
#define HASH_SELECTOBJECT         0x7CF4FD7C
#define HASH_SETBKCOLOR           0x5F1EBF5D
#define HASH_SETTEXTCOLOR         0x41936715
#define HASH_TEXTOUTA             0x805294C3
#define HASH_GDIFLUSH             0x0DD2A6FB
#define HASH_DELETEOBJECT         0xCC68186F
#define HASH_DELETEDC             0x9F3BEF5F 

// --- 2. REPLACE THIS WITH THE C++ BUILDER SCRIPT OUTPUT ---
#define TARGET_PIXEL_HASH       0x991ecb47 // The hash of srdnlen{fake_flag_for_testing}

// --- Windows Internals Structs (Ensures compilation without full SDK) ---
typedef struct _MY_LDR_DATA_TABLE_ENTRY {
    LIST_ENTRY InLoadOrderLinks;
    LIST_ENTRY InMemoryOrderLinks;
    LIST_ENTRY InInitializationOrderLinks;
    PVOID DllBase;
    PVOID EntryPoint;
    ULONG SizeOfImage;
    UNICODE_STRING FullDllName;
    UNICODE_STRING BaseDllName;
} MY_LDR_DATA_TABLE_ENTRY, *PMY_LDR_DATA_TABLE_ENTRY;

// --- Function Pointers Definitions ---
typedef HMODULE (WINAPI *pLoadLibraryA)(LPCSTR);
typedef HDC (WINAPI *pCreateCompatibleDC)(HDC);
typedef HBITMAP (WINAPI *pCreateDIBSection)(HDC, const BITMAPINFO*, UINT, VOID**, HANDLE, DWORD);
typedef HFONT (WINAPI *pCreateFontA)(int, int, int, int, int, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCSTR);
typedef HGDIOBJ (WINAPI *pSelectObject)(HDC, HGDIOBJ);
typedef COLORREF (WINAPI *pSetBkColor)(HDC, COLORREF);
typedef COLORREF (WINAPI *pSetTextColor)(HDC, COLORREF);
typedef BOOL (WINAPI *pTextOutA)(HDC, int, int, LPCSTR, int);
typedef BOOL (WINAPI *pGdiFlush)(void);
typedef BOOL (WINAPI *pDeleteObject)(HGDIOBJ);
typedef BOOL (WINAPI *pDeleteDC)(HDC);

// --- Hashing Functions ---
unsigned int HashStringC(const char* str) {
    unsigned int hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; 
    }
    return hash;
}

unsigned int HashPixels(const BYTE* data, size_t length) {
    unsigned int hash = 5381;
    for (size_t i = 0; i < length; i++) {
        hash = ((hash << 5) + hash) + data[i];
    }
    return hash;
}


HMODULE GetKernel32Base() {
    // Read the PEB on x64
    PBYTE pPeb = (PBYTE)__readgsqword(0x60);
    
    // In x64, the PEB_LDR_DATA pointer is at offset 0x18 in the PEB.
    // This bypasses MinGW's opaque struct definitions.
    PPEB_LDR_DATA pLdr = *((PPEB_LDR_DATA*)(pPeb + 0x18));
    
    PLIST_ENTRY pList = &pLdr->InMemoryOrderModuleList;
    
    // Walk the doubly-linked list
    PLIST_ENTRY pEntry = pList->Flink; // 1. exe itself
    pEntry = pEntry->Flink;            // 2. ntdll.dll
    pEntry = pEntry->Flink;            // 3. kernel32.dll
    
    PMY_LDR_DATA_TABLE_ENTRY pModule = CONTAINING_RECORD(pEntry, MY_LDR_DATA_TABLE_ENTRY, InMemoryOrderLinks);
    return (HMODULE)pModule->DllBase;
}


PVOID GetExportAddress(HMODULE hModule, unsigned int targetHash) {
    PBYTE pBase = (PBYTE)hModule;
    PIMAGE_DOS_HEADER pDos = (PIMAGE_DOS_HEADER)pBase;
    PIMAGE_NT_HEADERS pNt = (PIMAGE_NT_HEADERS)(pBase + pDos->e_lfanew);
    
    DWORD exportRVA = pNt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (exportRVA == 0) return nullptr;

    PIMAGE_EXPORT_DIRECTORY pExport = (PIMAGE_EXPORT_DIRECTORY)(pBase + exportRVA);
    PDWORD pNames = (PDWORD)(pBase + pExport->AddressOfNames);
    PDWORD pFuncs = (PDWORD)(pBase + pExport->AddressOfFunctions);
    PWORD pOrds = (PWORD)(pBase + pExport->AddressOfNameOrdinals);

    for (DWORD i = 0; i < pExport->NumberOfNames; i++) {
        char* pName = (char*)(pBase + pNames[i]);
        if (HashStringC(pName) == targetHash) {
            WORD ordinal = pOrds[i];
            return (PVOID)(pBase + pFuncs[ordinal]);
        }
    }
    return nullptr;
}

// --- Main Challenge Logic ---
int main() {
    // 1. Resolve kernel32.dll base manually
    HMODULE hKernel32 = GetKernel32Base();

    // 2. Resolve LoadLibraryA (so we can load user32/gdi32)
    pLoadLibraryA myLoadLibraryA = (pLoadLibraryA)GetExportAddress(hKernel32, HASH_LOADLIBRARYA);

    // 3. Stack strings to hide "user32.dll" and "gdi32.dll" from Ghidra strings output
    char user32_str[] = {'u','s','e','r','3','2','.','d','l','l','\0'};
    char gdi32_str[]  = {'g','d','i','3','2','.','d','l','l','\0'};
    HMODULE hUser32 = myLoadLibraryA(user32_str);
    HMODULE hGdi32  = myLoadLibraryA(gdi32_str);

    // 4. Resolve all GDI/User32 functions
    pCreateCompatibleDC myCreateCompatibleDC = (pCreateCompatibleDC)GetExportAddress(hGdi32, HASH_CREATECOMPATIBLEDC);
    pCreateDIBSection   myCreateDIBSection   = (pCreateDIBSection)GetExportAddress(hGdi32, HASH_CREATEDIBSECTION);
    pCreateFontA        myCreateFontA        = (pCreateFontA)GetExportAddress(hGdi32, HASH_CREATEFONTA);
    pSelectObject       mySelectObject       = (pSelectObject)GetExportAddress(hGdi32, HASH_SELECTOBJECT);
    pSetBkColor         mySetBkColor         = (pSetBkColor)GetExportAddress(hGdi32, HASH_SETBKCOLOR);
    pSetTextColor       mySetTextColor       = (pSetTextColor)GetExportAddress(hGdi32, HASH_SETTEXTCOLOR);
    pTextOutA           myTextOutA           = (pTextOutA)GetExportAddress(hGdi32, HASH_TEXTOUTA);
    pGdiFlush           myGdiFlush           = (pGdiFlush)GetExportAddress(hGdi32, HASH_GDIFLUSH);
    pDeleteObject       myDeleteObject       = (pDeleteObject)GetExportAddress(hGdi32, HASH_DELETEOBJECT);
    pDeleteDC           myDeleteDC           = (pDeleteDC)GetExportAddress(hGdi32, HASH_DELETEDC);

    // 5. Prompt for the flag
    std::cout << "> ";
    std::string userInput;
    std::cin >> userInput;

    // 6. Set up the invisible canvas (MAKE SURE THIS MATCHES YOUR BUILDER SCRIPT)
    int width = 450, height = 50;
    HDC hdc = myCreateCompatibleDC(NULL);

    BITMAPINFO bmi = { 0 };
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height; 
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void* pPixels = nullptr;
    HBITMAP hBitmap = myCreateDIBSection(hdc, &bmi, DIB_RGB_COLORS, &pPixels, NULL, 0);
    mySelectObject(hdc, hBitmap);

    // Stack string for font name
    char fontName[] = {'C','o','n','s','o','l','a','s','\0'};
    HFONT hFont = myCreateFontA(24, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, 
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, 
        NONANTIALIASED_QUALITY, DEFAULT_PITCH | FF_DONTCARE, fontName);
    mySelectObject(hdc, hFont);

    mySetBkColor(hdc, RGB(0, 0, 0));
    mySetTextColor(hdc, RGB(255, 255, 255));

    myTextOutA(hdc, 0, 0, userInput.c_str(), userInput.length());
    myGdiFlush();

    // --- REVERSIBLE VALIDATION ---
    size_t pixelSize = width * height * 4;
    BYTE* inputPixels = (BYTE*)pPixels;
    bool isCorrect = true;

    // Verify sizes match
    if (pixelSize == EXPECTED_PIXEL_SIZE) {
        for (size_t i = 0; i < pixelSize; i++) {
            // Check if the input pixel XOR'd with 0xAA matches our hardcoded array
            if ((inputPixels[i] ^ 0xAA) != EXPECTED_PIXELS[i]) {
                isCorrect = false;
                break;
            }
        }
    } else {
        isCorrect = false;
    }

    if (isCorrect) {
        std::cout << "Valid flag!\n";
    } else {
        std::cout << "Invalid flag.\n";
    }

    // Cleanup OS handles
    myDeleteObject(hFont);
    myDeleteObject(hBitmap);
    myDeleteDC(hdc);

    return 0;
}
