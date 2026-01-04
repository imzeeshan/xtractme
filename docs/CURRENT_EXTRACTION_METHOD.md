# Current Extraction Method

## Overview

Based on your current setup, here's how extraction is being done:

## Current Status

- **OCR Engine Selected**: MinerU (default)
- **File Type**: PDF
- **Pages Extracted**: 16 pages
- **JSON Data**: ❌ Not available (MinerU not installed)
- **Text Extraction**: ✅ Working (using PyMuPDF direct extraction)

## Extraction Flow

### 1. **Trigger Mechanism**

Extraction is triggered automatically via Django signals:

```
Document Saved → post_save signal → auto_process_document() → process_document_file()
```

**Triggered when:**
- Document created via Django admin ✅
- Document created via web form ✅
- Document created via API ✅
- Document updated with new file ✅

### 2. **Processing Flow** (`process_document_file`)

#### Step 1: File Type Detection
- Auto-detects file type from extension if not set
- Your document: `pdf` ✅

#### Step 2: OCR Engine Selection
- Checks `document.ocr_engine` field
- Your document: `mineru` ✅

#### Step 3: MinerU Attempt (if selected)
```python
if document.ocr_engine.lower() == 'mineru':
    pages_data = extract_pages_with_mineru_json(file_path)
    if pages_data:
        # Create pages with JSON data
        return
    else:
        # Fall back to traditional method
```

**Current Result**: MinerU not installed → Returns empty list → Falls back

#### Step 4: Traditional PDF Processing (Current Method)

Since MinerU is not available, the system uses **PyMuPDF (fitz)** for direct text extraction:

```python
# Open PDF with PyMuPDF
doc = fitz.open(file_path)
total_pages = len(doc)  # 16 pages

for each page:
    1. Extract text directly: page.get_text()
       - Works for PDFs with text layers (like yours)
       - No OCR needed if PDF has embedded text
    
    2. If no text found:
       - Render page to image
       - Try OCR (Tesseract/DeepSeek) if available
       - Currently: OCR not available, so page created with empty text
    
    3. Create Page object:
       - page_number
       - text (extracted from PDF)
       - json_data: None (not available without MinerU)
```

## Current Extraction Method: **PyMuPDF Direct Text Extraction**

### How It Works:

1. **Opens PDF**: Uses `fitz.open()` (PyMuPDF)
2. **Iterates Pages**: Loops through all pages (1-16)
3. **Extracts Text**: Uses `page.get_text()` - extracts text from PDF's text layer
4. **Creates Page Objects**: Stores text in database

### Advantages:
- ✅ Fast (no OCR processing needed)
- ✅ Accurate (uses PDF's native text layer)
- ✅ Works without additional dependencies
- ✅ Preserves formatting and structure

### Limitations:
- ❌ No JSON structure (only plain text)
- ❌ Won't work for scanned PDFs (images only)
- ❌ No bounding boxes or element positions
- ❌ No structured data extraction

## What Gets Stored

For your current document:

```python
Page.objects:
  - page_number: 1, 2, 3, ..., 16
  - text: "Extracted text content from PDF..."
  - json_data: None (empty/null)
  - image: None
```

## Comparison: MinerU vs Current Method

| Feature | MinerU (Not Installed) | Current (PyMuPDF) |
|---------|----------------------|-------------------|
| Text Extraction | ✅ Would work | ✅ Working |
| JSON Structure | ✅ Would provide | ❌ Not available |
| Page-by-page JSON | ✅ Would provide | ❌ Not available |
| Bounding Boxes | ✅ Would provide | ❌ Not available |
| Element Detection | ✅ Would provide | ❌ Not available |
| Speed | Slower | Faster |
| Dependencies | Requires MinerU | Built-in (PyMuPDF) |

## To Get JSON Extraction Working

Install MinerU:

```bash
pip install mineru
```

Then reprocess:
```bash
python manage.py reprocess_documents --all
```

This will:
1. Extract pages with MinerU
2. Store JSON data for each page
3. Provide structured data with bounding boxes, elements, etc.

## Current Extraction Summary

**Method**: PyMuPDF Direct Text Extraction  
**Status**: ✅ Working  
**Pages**: 16 pages extracted  
**Text**: ✅ Available  
**JSON**: ❌ Not available (requires MinerU)  
**OCR**: Not needed (PDF has text layers)  

The extraction is working correctly - it's extracting text from your PDF's text layers. To get JSON data and structured extraction, you'll need to install MinerU.

