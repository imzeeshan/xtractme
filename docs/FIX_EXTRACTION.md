# Fix: Extraction Not Triggered

## Problem
Extraction was not being triggered when documents were created via Django admin.

## Solution Implemented

### 1. Django Signals (Automatic Extraction)
Created `core/signals.py` with a `post_save` signal that automatically processes documents when they are saved, regardless of how they were created (admin, API, web form, etc.).

**Features:**
- Automatically triggers extraction on document save
- Works for both new documents and updates
- Handles file type detection automatically
- Logs errors without breaking the save operation

### 2. Admin Override
Updated `DocumentAdmin` to:
- Set file_type automatically if not set
- Show success/warning messages after save
- Provide "Reprocess documents" admin action

### 3. Management Command
Created `reprocess_documents` command to reprocess existing documents:

```bash
# Reprocess all documents
python manage.py reprocess_documents --all

# Reprocess specific documents
python manage.py reprocess_documents 1 2 3
```

## How to Use

### For Existing Documents (Like "Test Document")

**Option 1: Using Management Command**
```bash
python manage.py reprocess_documents --all
```

**Option 2: Using Django Admin**
1. Go to Django admin
2. Select the document(s) you want to reprocess
3. Choose "Reprocess selected documents (extract pages)" from the Actions dropdown
4. Click "Go"

**Option 3: Using Django Shell**
```python
from core.models import Document
from core.views import process_document_file

doc = Document.objects.get(title="Test Document")
doc.pages.all().delete()  # Clear existing pages
process_document_file(doc)  # Reprocess
```

### For New Documents

Now extraction will happen automatically when:
- Creating documents via Django admin ✅
- Creating documents via web form ✅
- Creating documents via API ✅
- Updating documents with new files ✅

## Testing

To test that signals are working:

1. **Restart Django server** (signals need to be loaded):
   ```bash
   python manage.py runserver
   ```

2. **Create a new document in admin:**
   - Go to `/admin/core/document/add/`
   - Upload a PDF file
   - Select "mineru" as OCR engine
   - Save
   - Check that pages are automatically created

3. **Reprocess existing document:**
   ```bash
   python manage.py reprocess_documents --all
   ```

## Troubleshooting

### Issue: Signals not working

**Solution:**
- Make sure `core/apps.py` has the `ready()` method that imports signals
- Restart Django server (signals are loaded at startup)
- Check Django logs for signal errors

### Issue: "No pages extracted"

**Possible causes:**
- File is empty or corrupted
- OCR engine not installed (MinerU, Tesseract, etc.)
- File path issues
- Processing errors (check logs)

**Solution:**
- Check that required dependencies are installed: `pip install -r requirements.txt`
- Verify the file exists and is readable
- Check Django logs for detailed error messages

### Issue: Processing fails silently

**Solution:**
- Check Django logs: `python manage.py runserver --verbosity 2`
- Check signal logs (errors are logged but don't break save)
- Use management command for better error visibility

## Files Changed

1. **`core/signals.py`** - New file with signal handlers
2. **`core/apps.py`** - Updated to register signals
3. **`core/admin.py`** - Added reprocess action and save override
4. **`core/management/commands/reprocess_documents.py`** - New management command

## Next Steps

1. **Reprocess your existing "Test Document":**
   ```bash
   python manage.py reprocess_documents --all
   ```

2. **Verify extraction works:**
   - Check that pages are created
   - Check that JSON data is stored (if using MinerU)
   - View document detail page to see extracted content

3. **Test automatic extraction:**
   - Create a new document in admin
   - Verify pages are automatically created
   - Check success message shows page count

