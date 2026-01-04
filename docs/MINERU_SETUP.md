# MinerU Integration Guide

MinerU is now set as the **default OCR engine** for this Django document management application.

## What is MinerU?

MinerU is a powerful document understanding tool designed for processing academic papers and documents. It provides:
- Advanced PDF parsing and text extraction
- Better handling of complex document layouts
- Improved accuracy for academic and technical documents
- Structured output with page-level information

## Installation

### Step 1: Install MinerU

```bash
pip install mineru
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python -c "from mineru import MagicPDF; print('MinerU installed successfully')"
```

## Usage

### Default Behavior

- **New documents** will automatically use MinerU as the OCR engine
- The form dropdown shows "MinerU (Default)" as the first option
- Existing documents retain their original OCR engine setting

### Changing OCR Engine

You can still choose other OCR engines:
- **MinerU (Default)** - Best for PDFs and academic documents
- **Tesseract OCR** - Traditional OCR engine, good for images
- **DeepSeek OCR** - Alternative OCR engine

## How It Works

### For PDF Files

1. When a PDF is uploaded with MinerU selected:
   - MinerU processes the entire PDF document
   - Extracts text with better layout understanding
   - Creates Page objects with extracted text

2. If MinerU is not available or fails:
   - The system automatically falls back to traditional PDF processing
   - Uses PyMuPDF for text extraction
   - Falls back to Tesseract/DeepSeek for OCR if needed

### For Image Files

- MinerU can process images, but PDFs are its primary strength
- For images, Tesseract or DeepSeek may provide better results
- The system will attempt MinerU first, then fall back if needed

## Configuration

The default OCR engine is configured in `core/models.py`:

```python
ocr_engine = models.CharField(max_length=50, default='mineru')
```

To change the default, modify this field's default value.

## Troubleshooting

### Issue: "MinerU is not installed"

**Solution:**
```bash
pip install mineru
```

### Issue: MinerU fails to process a document

**Solutions:**
1. The system automatically falls back to traditional processing
2. Try switching to Tesseract or DeepSeek OCR for that specific document
3. Check that the PDF is not corrupted or password-protected

### Issue: Slow processing

**Note:** MinerU may be slower than Tesseract for simple documents, but provides better accuracy for complex layouts.

**Solutions:**
1. For simple documents, consider using Tesseract
2. Ensure you have sufficient system resources
3. MinerU benefits from GPU acceleration if available

## Migration Notes

If you have existing documents in the database:

- Existing documents keep their original OCR engine setting
- Only new documents will default to MinerU
- You can update existing documents to use MinerU through the edit interface

## Performance Tips

1. **For Academic Papers**: Use MinerU (default) - best results
2. **For Simple Documents**: Tesseract may be faster
3. **For Images**: Tesseract or DeepSeek often work better
4. **For Complex PDFs**: MinerU provides superior layout understanding

## Resources

- MinerU GitHub: https://github.com/opendatalab/MinerU
- MinerU Documentation: https://mineru.readthedocs.io/
- PyPI Package: https://pypi.org/project/mineru/

## Code Changes Summary

1. **Models**: Default OCR engine changed from 'tesseract' to 'mineru'
2. **Forms**: Added MinerU as first option in dropdown
3. **OCR Utils**: Added `extract_text_with_mineru()` function
4. **Views**: Updated to handle MinerU processing for both PDFs and images
5. **Requirements**: Added `mineru>=0.1.0` to requirements.txt

