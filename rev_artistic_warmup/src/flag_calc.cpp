#include <windows.h>
#include <iostream>
#include <stdio.h>

int main() {
    const char* flag = "srdnlen{pl5_Charles_w1n_th3_champ1on5hip}";
    int width = 450; 
    int height = 50;

    HDC hdc = CreateCompatibleDC(NULL);
    BITMAPINFO bmi = { 0 };
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height; 
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void* pPixels = nullptr;
    HBITMAP hBitmap = CreateDIBSection(hdc, &bmi, DIB_RGB_COLORS, &pPixels, NULL, 0);
    SelectObject(hdc, hBitmap);

    HFONT hFont = CreateFontA(24, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, 
        OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, NONANTIALIASED_QUALITY, DEFAULT_PITCH | FF_DONTCARE, "Consolas");
    SelectObject(hdc, hFont);

    SetBkColor(hdc, RGB(0, 0, 0));
    SetTextColor(hdc, RGB(255, 255, 255));
    TextOutA(hdc, 0, 0, flag, strlen(flag));
    GdiFlush();

    // --- NEW: DUMP PIXELS TO A HEADER FILE ---
    size_t pixelDataSize = width * height * 4; 
    BYTE* rawPixels = (BYTE*)pPixels;

    FILE* file = fopen("expected_pixels.h", "w");
    fprintf(file, "const size_t EXPECTED_PIXEL_SIZE = %zu;\n", pixelDataSize);
    fprintf(file, "const unsigned char EXPECTED_PIXELS[] = {\n");
    
    for (size_t i = 0; i < pixelDataSize; i++) {
        // XOR pixels with 0xAA
        fprintf(file, "0x%02X, ", rawPixels[i] ^ 0xAA);
        if ((i + 1) % 16 == 0) fprintf(file, "\n");
    }
    fprintf(file, "};\n");
    fclose(file);

    std::cout << "Done! Generated 'expected_pixels.h' (" << pixelDataSize << " bytes).\n";

    DeleteObject(hFont);
    DeleteObject(hBitmap);
    DeleteDC(hdc);
    return 0;
}
