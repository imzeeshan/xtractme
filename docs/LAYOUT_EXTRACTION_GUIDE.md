# Layout Extraction and Usage Guide

## Overview

This guide explains how to access and use layout information from OCR libraries that preserve document structure. The application supports layout-aware OCR through **MinerU** (primary) and **PaddleOCR** (enhanced).

## OCR Libraries with Layout Support

### 1. MinerU (Recommended) ⭐
- **Best for**: Complex documents with tables, formulas, multi-column layouts
- **Layout Features**:
  - Document structure detection (paragraphs, headings, tables, formulas)
  - Bounding box coordinates for all elements
  - Element relationships and hierarchy
  - Page-by-page structured JSON output

### 2. PaddleOCR (Enhanced)
- **Best for**: Text-heavy documents with basic layout needs
- **Layout Features**:
  - Bounding box coordinates for text lines
  - Text line positions and confidence scores
  - Basic spatial information

### 3. Donut (Document Understanding Transformer)
- **Best for**: Structured document understanding
- **Layout Features**:
  - JSON structure with layout information
  - Can be enhanced to extract full layout data

## Accessing Layout Information

### Via Django Models

The `Page` model provides several helper methods to extract layout information:

```python
from core.models import Page

# Get a page
page = Page.objects.get(pk=1)

# Check if layout data is available
if page.json_data:
    # Extract all blocks (paragraphs, headings, etc.)
    blocks = page.get_blocks()
    
    # Extract specific element types
    tables = page.get_tables()
    formulas = page.get_formulas()
    headings = page.get_headings()
    paragraphs = page.get_paragraphs()
    
    # Get all bounding boxes
    bboxes = page.get_bounding_boxes()
    
    # Get complete layout structure
    layout = page.get_layout_structure()
    
    # Extract text by block type
    paragraph_texts = page.extract_text_by_type('paragraph')
```

### Example: Working with Layout Data

```python
from core.models import Page, Document

# Get a document
doc = Document.objects.get(pk=1)

# Process all pages
for page in doc.pages.all():
    if page.json_data:
        print(f"Page {page.page_number}:")
        print(f"  - {len(page.get_blocks())} blocks")
        print(f"  - {len(page.get_tables())} tables")
        print(f"  - {len(page.get_formulas())} formulas")
        print(f"  - {len(page.get_headings())} headings")
        
        # Get all bounding boxes
        for bbox_info in page.get_bounding_boxes():
            print(f"    {bbox_info['type']}: {bbox_info['text'][:50]}...")
            print(f"      BBox: {bbox_info['bbox']}")
```

## MinerU JSON Structure

MinerU provides rich structured data. Here's the typical structure:

```json
{
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {
          "type": "heading",
          "text": "Document Title",
          "bbox": [x, y, width, height],
          "level": 1
        },
        {
          "type": "paragraph",
          "text": "Paragraph content...",
          "bbox": [x, y, width, height]
        },
        {
          "type": "table",
          "text": "Table content...",
          "bbox": [x, y, width, height],
          "rows": [...],
          "columns": [...]
        },
        {
          "type": "formula",
          "text": "E = mc²",
          "bbox": [x, y, width, height]
        }
      ]
    }
  ]
}
```

## PaddleOCR Layout Structure

PaddleOCR provides text line-level layout information:

```json
{
  "blocks": [
    {
      "type": "text_line",
      "text": "Line of text",
      "bbox": [x, y, width, height],
      "confidence": 0.95,
      "bbox_coords": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    }
  ],
  "ocr_engine": "paddleocr",
  "page_width": 800,
  "page_height": 1200
}
```

## Practical Use Cases

### 1. Extract Tables Only

```python
def extract_all_tables(document_id):
    """Extract all tables from a document"""
    doc = Document.objects.get(pk=document_id)
    all_tables = []
    
    for page in doc.pages.all():
        tables = page.get_tables()
        for table in tables:
            all_tables.append({
                'page': page.page_number,
                'text': table.get('text', ''),
                'bbox': table.get('bbox'),
                'raw_data': table
            })
    
    return all_tables
```

### 2. Find Text by Position

```python
def find_text_in_region(page, x, y, width, height):
    """Find all text blocks within a specific region"""
    blocks = page.get_blocks()
    matching_blocks = []
    
    for block in blocks:
        bbox = block.get('bbox')
        if bbox:
            bx, by, bw, bh = bbox
            # Check if block overlaps with region
            if (bx < x + width and bx + bw > x and
                by < y + height and by + bh > y):
                matching_blocks.append(block)
    
    return matching_blocks
```

### 3. Extract Document Structure

```python
def get_document_outline(document_id):
    """Extract document outline from headings"""
    doc = Document.objects.get(pk=document_id)
    outline = []
    
    for page in doc.pages.all():
        headings = page.get_headings()
        for heading in headings:
            outline.append({
                'page': page.page_number,
                'level': heading.get('level', 1),
                'text': heading.get('text', ''),
                'bbox': heading.get('bbox')
            })
    
    return outline
```

### 4. Reconstruct Document with Layout

```python
def reconstruct_document_with_layout(document_id):
    """Reconstruct document preserving layout structure"""
    doc = Document.objects.get(pk=document_id)
    document_structure = {
        'title': doc.title,
        'pages': []
    }
    
    for page in doc.pages.all():
        if page.json_data:
            page_structure = {
                'page_number': page.page_number,
                'blocks': []
            }
            
            blocks = page.get_blocks()
            for block in blocks:
                page_structure['blocks'].append({
                    'type': block.get('type'),
                    'text': block.get('text', ''),
                    'bbox': block.get('bbox'),
                    'metadata': {k: v for k, v in block.items() 
                                if k not in ['type', 'text', 'bbox']}
                })
            
            document_structure['pages'].append(page_structure)
    
    return document_structure
```

## Using Layout in Views

### Example View: Display Layout Information

```python
from django.shortcuts import render, get_object_or_404
from core.models import Document

def document_layout_view(request, pk):
    """Display document with layout information"""
    doc = get_object_or_404(Document, pk=pk)
    
    # Collect layout statistics
    layout_stats = {
        'total_blocks': 0,
        'total_tables': 0,
        'total_formulas': 0,
        'total_headings': 0,
        'pages_with_layout': 0
    }
    
    pages_data = []
    for page in doc.pages.all():
        if page.json_data:
            layout_stats['pages_with_layout'] += 1
            layout_stats['total_blocks'] += len(page.get_blocks())
            layout_stats['total_tables'] += len(page.get_tables())
            layout_stats['total_formulas'] += len(page.get_formulas())
            layout_stats['total_headings'] += len(page.get_headings())
            
            pages_data.append({
                'page': page,
                'layout': page.get_layout_structure()
            })
    
    return render(request, 'core/document_layout.html', {
        'document': doc,
        'layout_stats': layout_stats,
        'pages_data': pages_data
    })
```

## API Usage

### Access via Django Shell

```python
python manage.py shell

from core.models import Page

# Get a page with layout
page = Page.objects.filter(json_data__isnull=False).first()

# Access JSON directly
json_data = page.json_data

# Use helper methods
blocks = page.get_blocks()
tables = page.get_tables()
headings = page.get_headings()

# Get formatted JSON
formatted = page.get_json_preview()
```

## Best Practices

### 1. Always Check for Layout Data

```python
if page.json_data:
    # Layout data available
    blocks = page.get_blocks()
else:
    # Fallback to plain text
    text = page.text
```

### 2. Handle Different OCR Engines

```python
def get_layout_data(page):
    """Get layout data regardless of OCR engine"""
    if page.json_data:
        ocr_engine = page.json_data.get('ocr_engine', 'mineru')
        
        if ocr_engine == 'mineru':
            return page.get_blocks()
        elif ocr_engine == 'paddleocr':
            return page.json_data.get('blocks', [])
    
    return []
```

### 3. Cache Layout Queries

```python
from django.core.cache import cache

def get_cached_layout(page_id):
    """Get cached layout structure"""
    cache_key = f'page_layout_{page_id}'
    layout = cache.get(cache_key)
    
    if not layout:
        page = Page.objects.get(pk=page_id)
        layout = page.get_layout_structure()
        cache.set(cache_key, layout, 3600)  # Cache for 1 hour
    
    return layout
```

## Troubleshooting

### Issue: No layout data available

**Solution**: 
- Ensure the document was processed with MinerU or enhanced PaddleOCR
- Check that `page.json_data` is not None
- Reprocess the document with MinerU selected

### Issue: Layout structure differs from expected

**Solution**:
- MinerU JSON structure may vary by version
- Check the actual structure: `page.get_json_preview()`
- Use the helper methods which handle different structures

### Issue: Bounding boxes are incorrect

**Solution**:
- Verify coordinate system (MinerU uses PDF coordinates)
- Check page dimensions in JSON data
- Normalize coordinates if needed for display

## Advanced Usage

### Custom Layout Processing

```python
def process_custom_layout(page):
    """Process layout data for custom use case"""
    if not page.json_data:
        return None
    
    # Custom processing logic
    processed = {
        'text_regions': [],
        'non_text_regions': []
    }
    
    blocks = page.get_blocks()
    for block in blocks:
        block_type = block.get('type', '').lower()
        if 'text' in block_type or 'paragraph' in block_type:
            processed['text_regions'].append(block)
        else:
            processed['non_text_regions'].append(block)
    
    return processed
```

## Summary

- **MinerU** is the best choice for complex layout extraction
- Use `Page` model helper methods for easy access to layout data
- Layout data is stored in `json_data` JSONField
- Helper methods handle different JSON structures automatically
- Always check if `json_data` exists before accessing layout

For more information, see:
- `docs/MINERU_JSON_FEATURE.md` - MinerU JSON feature details
- `docs/MINERU_SETUP.md` - MinerU installation guide
