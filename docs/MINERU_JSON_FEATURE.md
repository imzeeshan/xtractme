# MinerU JSON Extraction Feature

## Overview

The application now automatically extracts and stores page-by-page JSON data from PDFs when using MinerU as the OCR engine. This allows you to preview PDF pages alongside their structured JSON data.

## Features

### 1. Automatic JSON Extraction
- When a document is saved with MinerU selected, the system automatically:
  - Processes the PDF with MinerU
  - Extracts structured JSON data for each page
  - Stores both text and JSON in the database

### 2. Page Preview with JSON
- View individual PDF pages with their corresponding JSON data
- Side-by-side comparison of PDF preview and JSON structure
- Navigate between pages easily

### 3. Database Storage
- Each `Page` model now includes a `json_data` JSONField
- Stores the complete MinerU output structure for each page
- Includes text, bounding boxes, elements, and other metadata

## How It Works

### When a Document is Saved

1. **Document Upload**: User uploads a PDF and selects MinerU as OCR engine
2. **MinerU Processing**: The system calls `extract_pages_with_mineru_json()`
3. **Page Creation**: For each page in the PDF:
   - Extracts text content
   - Extracts structured JSON data
   - Creates a `Page` object with both text and JSON

### JSON Structure

The JSON data stored includes:
- **text**: Extracted text content
- **bbox**: Bounding box coordinates (if available)
- **elements**: Structured elements like paragraphs, headings, tables
- **metadata**: Additional MinerU processing information

Example JSON structure:
```json
{
  "text": "Page content here...",
  "bbox": [x, y, width, height],
  "elements": [
    {
      "type": "paragraph",
      "text": "...",
      "bbox": [...]
    }
  ]
}
```

## Usage

### Viewing Page Previews

1. Navigate to a document detail page
2. Click "Preview with JSON" on any page
3. View the PDF page preview alongside its JSON data
4. Use navigation buttons to move between pages

### Accessing JSON Data

**Via Web Interface:**
- Go to document detail page
- Click "Preview with JSON" on any page
- JSON is displayed in a formatted, scrollable view
- Click "Copy JSON" to copy to clipboard

**Via Django Admin:**
- Go to `/admin/core/page/`
- Click on any page
- View JSON data in the "MinerU JSON Data" section

**Via API/Code:**
```python
from core.models import Page

page = Page.objects.get(pk=1)
json_data = page.json_data  # Direct access to JSON
formatted_json = page.get_json_preview()  # Formatted string
```

## Database Changes

### Migration Applied
- Added `json_data` JSONField to `Page` model
- Field is nullable and optional (for backward compatibility)
- Existing pages without JSON data will show a warning message

### Model Updates

```python
class Page(models.Model):
    # ... existing fields ...
    json_data = models.JSONField(blank=True, null=True)
    
    def get_json_preview(self):
        """Return formatted JSON string for display"""
        if self.json_data:
            return json.dumps(self.json_data, indent=2, ensure_ascii=False)
        return None
```

## URL Routes

- **Page Preview**: `/pages/<page_id>/preview/`
- **Document Detail**: `/documents/<document_id>/`

## Templates

### New Templates
- `core/page_preview.html` - Page preview with PDF and JSON side-by-side

### Updated Templates
- `core/document_detail.html` - Added "Preview with JSON" buttons for each page

## Admin Interface

### Page Admin Updates
- Added `has_json` column to list view
- Added JSON preview in detail view
- JSON data shown in collapsible section

## Technical Details

### OCR Utils Function

```python
def extract_pages_with_mineru_json(file_path):
    """
    Extract page-by-page JSON data from PDF using MinerU
    
    Returns:
        list: List of dictionaries with:
            - page_number: int
            - text: str
            - json_data: dict
    """
```

### Processing Flow

1. **MinerU Processing**: `mineru_processor.parse(file_path)`
2. **Data Extraction**: Parse MinerU output structure
3. **Page Creation**: Create Page objects with text and JSON
4. **Fallback**: If MinerU fails, falls back to traditional processing

## Troubleshooting

### Issue: No JSON data for existing pages

**Solution**: 
- Re-upload the document with MinerU selected
- Or manually reprocess using Django admin

### Issue: MinerU returns unexpected format

**Solution**: 
- The code handles multiple MinerU output formats
- Check the JSON structure in the preview page
- MinerU output format may vary by version

### Issue: JSON preview not showing

**Solution**:
- Ensure the page was processed with MinerU
- Check browser console for JavaScript errors
- Verify JSON data exists: `page.json_data` should not be None

## Future Enhancements

Potential improvements:
- Export JSON data for all pages
- Search within JSON data
- Visual highlighting of elements on PDF preview
- JSON schema validation
- Batch processing for multiple documents

## Notes

- JSON extraction only works with MinerU OCR engine
- Documents processed with other OCR engines won't have JSON data
- JSON structure depends on MinerU version and document complexity
- Large PDFs may take longer to process

