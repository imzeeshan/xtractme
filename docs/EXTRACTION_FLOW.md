# Document Extraction Flow

## How Extraction is Triggered

The extraction process is **manually triggered** in the view functions when a document is created or updated. It is **NOT** automatically triggered by Django signals.

## Extraction Trigger Points

### 1. Document Creation (`document_create` view)

**Location**: `core/views.py` - `document_create()` function

**Flow**:
1. User submits form with file upload
2. Form validation passes
3. Document object is created and saved to database
4. **`process_document_file(document)` is called explicitly**
5. Extraction runs synchronously
6. User is redirected to document detail page

**Code Flow**:
```python
def document_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            # ... set file_type ...
            document.save()  # Document saved to DB
            
            # ⚡ EXTRACTION TRIGGERED HERE
            try:
                process_document_file(document)
                messages.success(request, 'Document created successfully!')
                return redirect('document_detail', pk=document.pk)
            except Exception as e:
                # If extraction fails, document is deleted
                document.delete()
```

### 2. Document Update (`document_update` view)

**Location**: `core/views.py` - `document_update()` function

**Flow**:
1. User submits update form (optionally with new file)
2. Form validation passes
3. If a new file is uploaded:
   - Old pages are deleted
   - **`process_document_file(document)` is called explicitly**
   - Extraction runs synchronously
4. User is redirected to document detail page

**Code Flow**:
```python
def document_update(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            
            if 'file' in request.FILES:  # New file uploaded
                # ... set file_type ...
                document.pages.all().delete()  # Delete old pages
                
                # ⚡ EXTRACTION TRIGGERED HERE
                try:
                    process_document_file(document)
                except Exception as e:
                    # Handle error
```

## Extraction Process (`process_document_file` function)

**Location**: `core/views.py` - `process_document_file()` function

**What Happens**:
1. Checks document file type (PDF or image)
2. Checks OCR engine selection
3. **If MinerU is selected**:
   - Calls `extract_pages_with_mineru_json(file_path)`
   - Creates Page objects with both text and JSON data
4. **If other OCR engine**:
   - Uses traditional processing methods
   - Creates Page objects with text only

**Code Flow**:
```python
def process_document_file(document):
    file_path = document.file.path
    
    if document.file_type == 'pdf':
        if document.ocr_engine.lower() == 'mineru':
            # ⚡ MINERU JSON EXTRACTION
            pages_data = extract_pages_with_mineru_json(file_path)
            
            # Create Page objects with JSON
            for page_info in pages_data:
                Page.objects.create(
                    document=document,
                    page_number=page_info['page_number'],
                    text=page_info.get('text', ''),
                    json_data=page_info.get('json_data', {})  # JSON stored here
                )
        else:
            # Traditional OCR processing
            # ...
```

## Important Notes

### ⚠️ Synchronous Processing
- Extraction runs **synchronously** during the HTTP request
- User must wait for extraction to complete before seeing results
- Large PDFs may cause timeout issues

### ⚠️ No Automatic Triggering
- Extraction is **NOT** triggered by Django signals (`post_save`, etc.)
- Extraction only happens when:
  - Creating a new document via web form
  - Updating a document with a new file via web form
- Documents created via Django admin or API won't trigger extraction automatically

### ⚠️ Error Handling
- If extraction fails during creation, the document is deleted
- If extraction fails during update, an error message is shown
- User can retry by uploading again

## Alternative: Using Django Signals (Not Currently Implemented)

If you want automatic extraction whenever a document is saved (including via admin or API), you could add a signal:

```python
# In core/signals.py (create this file)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Document
from .views import process_document_file

@receiver(post_save, sender=Document)
def auto_extract_on_save(sender, instance, created, **kwargs):
    """Automatically extract pages when document is saved"""
    if created and instance.file:
        process_document_file(instance)
```

Then register it in `core/apps.py`:
```python
class CoreConfig(AppConfig):
    def ready(self):
        import core.signals
```

## Current Implementation Summary

| Trigger Point | When | Extraction Runs |
|---------------|------|-----------------|
| Web Form Create | User uploads new document | ✅ Yes |
| Web Form Update | User uploads new file | ✅ Yes |
| Django Admin | Admin creates/updates document | ❌ No |
| API/Code | Programmatic document creation | ❌ No |
| Signal-based | Any save operation | ❌ No (not implemented) |

## Recommendations

1. **For Production**: Consider using Celery or similar for async processing
2. **For Admin/API**: Add signal-based extraction if needed
3. **For Large Files**: Implement background task processing
4. **For Better UX**: Show processing status/progress indicator

