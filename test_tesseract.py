"""Test script to verify Tesseract OCR detection"""
import os
import shutil
import sys

print("=" * 60)
print("Tesseract OCR Detection Test")
print("=" * 60)

# Check 1: Is pytesseract installed?
try:
    import pytesseract
    print("[OK] pytesseract is installed")
except ImportError:
    print("X pytesseract is NOT installed")
    sys.exit(1)

# Check 2: Is tesseract in PATH?
tesseract_in_path = shutil.which('tesseract')
if tesseract_in_path:
    print(f"[OK] Tesseract found in PATH: {tesseract_in_path}")
else:
    print("[X] Tesseract NOT found in PATH")

# Check 3: Check common Windows installation paths
common_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]
username = os.getenv('USERNAME', '')
if username:
    common_paths.append(
        r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(username)
    )

found_paths = []
for path in common_paths:
    if os.path.exists(path):
        found_paths.append(path)
        print(f"[OK] Found Tesseract at: {path}")

if not found_paths and not tesseract_in_path:
    print("[X] Tesseract NOT found in standard locations")

# Check 4: Try to get version (this will test if pytesseract can find it)
print("\n" + "=" * 60)
print("Testing pytesseract.get_tesseract_version()...")
print("=" * 60)

try:
    # First try without setting path
    try:
        version = pytesseract.get_tesseract_version()
        print(f"[OK] Tesseract version (auto-detected): {version}")
        print(f"  Command path: {getattr(pytesseract.pytesseract, 'tesseract_cmd', 'Not set')}")
    except Exception as e:
        print(f"[X] Auto-detection failed: {e}")
        
        # Try setting path manually if we found one
        if found_paths:
            pytesseract.pytesseract.tesseract_cmd = found_paths[0]
            try:
                version = pytesseract.get_tesseract_version()
                print(f"[OK] Tesseract version (after manual setup): {version}")
                print(f"  Command path: {pytesseract.pytesseract.tesseract_cmd}")
            except Exception as e2:
                print(f"[X] Still failed after manual setup: {e2}")
        elif tesseract_in_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
            try:
                version = pytesseract.get_tesseract_version()
                print(f"[OK] Tesseract version (after setting PATH): {version}")
                print(f"  Command path: {pytesseract.pytesseract.tesseract_cmd}")
            except Exception as e2:
                print(f"[X] Still failed after setting PATH: {e2}")
except Exception as e:
    print(f"[X] Error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
if tesseract_in_path or found_paths:
    print("Tesseract IS installed but may need configuration")
else:
    print("Tesseract is NOT installed")
    print("\nTo install:")
    print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. Install and check 'Add to PATH'")
    print("3. Or set TESSERACT_CMD in .env file")
