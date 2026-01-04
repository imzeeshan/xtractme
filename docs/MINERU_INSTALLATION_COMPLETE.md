# MinerU Installation and Configuration Complete

## Installation Status

✅ **MinerU is installed and configured**

### Installed Packages
- `mineru` (v2.6.8)
- `doclayout-yolo` (v0.0.4) - Required for layout detection
- `ultralytics` (v8.3.240) - Required for YOLO models
- All dependencies are installed

### Configuration

The code has been updated to use MinerU's `do_parse` function from `mineru.cli.common`, which:
- Processes PDF files using MinerU's pipeline backend
- Extracts structured JSON data page-by-page
- Outputs to temporary directories and reads the results
- Falls back gracefully if MinerU is not available

## How It Works

### For PDF Processing

1. **When a document is saved with MinerU selected:**
   - The `extract_pages_with_mineru_json()` function is called
   - It reads the PDF file as bytes
   - Calls MinerU's `do_parse()` function with:
     - PDF bytes
     - Language list (default: English)
     - Pipeline backend
     - Auto parse method
     - Formula and table extraction enabled

2. **MinerU Processing:**
   - Downloads model weights automatically on first use (if not already cached)
   - Processes the PDF page-by-page
   - Generates structured JSON output (`middle_json.json`)
   - Extracts text from blocks within each page

3. **Data Extraction:**
   - Reads the `middle_json.json` file from the output directory
   - Extracts page-by-page data:
     - Page number
     - Text content (from blocks)
     - Full JSON structure for each page
   - Creates `Page` objects in Django with the extracted data

### Model Weights

MinerU automatically downloads model weights from HuggingFace on first use:
- Models are cached in `~/.cache/huggingface/` (or similar location)
- First run may take several minutes to download models
- Subsequent runs will use cached models

### Fallback Behavior

If MinerU fails or is not available:
- The system falls back to traditional PDF text extraction using PyMuPDF
- No errors are raised - graceful degradation
- Pages are still created with extracted text

## Testing

To test MinerU:

```bash
# Using Django shell
python manage.py shell
>>> from core.models import Document
>>> from core.views import process_document_file
>>> doc = Document.objects.get(pk=2)  # Use your document ID
>>> doc.pages.all().delete()  # Clear existing pages
>>> process_document_file(doc)  # Reprocess with MinerU
>>> print(f"Pages: {doc.pages.count()}")
>>> page = doc.pages.first()
>>> print(f"Has JSON: {bool(page.json_data)}")
```

## Files Modified

1. **`core/ocr_utils.py`**:
   - Updated `extract_text_with_mineru()` to use `do_parse`
   - Updated `extract_pages_with_mineru_json()` to use `do_parse` and read JSON output
   - Added proper error handling and fallback

## Next Steps

1. **First Run**: The first time MinerU processes a document, it will download model weights (this may take several minutes)

2. **Monitor Logs**: Check Django logs for MinerU processing information

3. **View Results**: After processing, check the document detail page to see:
   - Extracted text per page
   - JSON data preview for each page
   - Page-by-page PDF preview with JSON

## Troubleshooting

### If MinerU fails to process:

1. **Check Model Download**: First run downloads models - wait for completion
2. **Check Logs**: Look for error messages in Django logs
3. **Verify Installation**: Run `python -c "from mineru.cli.common import do_parse; print('OK')"`
4. **Fallback**: The system will automatically fall back to PyMuPDF if MinerU fails

### Common Issues:

- **Slow First Run**: Normal - models are being downloaded
- **Memory Issues**: MinerU requires significant RAM (16GB+ recommended)
- **GPU**: Optional but recommended for faster processing

## Configuration Options

You can customize MinerU behavior by modifying `extract_pages_with_mineru_json()` in `core/ocr_utils.py`:

- **Language**: Change `lang_list = ['en']` to other languages (e.g., `['ch']` for Chinese)
- **Parse Method**: Change `parse_method='auto'` to `'txt'` or `'ocr'`
- **Backend**: Currently using `'pipeline'` backend (most general)

## Status

✅ Installation: Complete
✅ Configuration: Complete  
✅ Code Integration: Complete
⏳ Testing: In Progress (models downloading on first use)

