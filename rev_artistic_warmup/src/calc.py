def djb2_hash(func_name):
    hash_val = 5381
    for char in func_name:
        hash_val = ((hash_val << 5) + hash_val) + ord(char)
        hash_val &= 0xFFFFFFFF
    return hash_val

apis = [
    "LoadLibraryA", "CreateCompatibleDC", "CreateDIBSection", 
    "CreateFontA", "SelectObject", "SetBkColor", "SetTextColor", 
    "TextOutA", "GdiFlush", "DeleteObject", "DeleteDC"
]

for api in apis:
    print(f"#define HASH_{api.upper():<20} 0x{djb2_hash(api):08X}")
    