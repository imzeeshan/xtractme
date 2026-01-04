"""
Django signals for automatic document processing
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import Document
import logging

logger = logging.getLogger(__name__)


# Store original OCR engine in pre_save to detect changes
_original_ocr_engine = {}

@receiver(post_save, sender=Document)
def auto_process_document(sender, instance, created, **kwargs):
    """
    Automatically process document file when saved.
    This triggers extraction for documents created via admin, API, or any other method.
    """
    # Only process if document has a file
    if not instance.file:
        return
    
    # Check if pages already exist (to avoid reprocessing)
    has_pages = instance.pages.exists()
    
    # Check if OCR engine was changed (need to reprocess if it changed)
    ocr_engine_changed = False
    if not created and has_pages and instance.pk in _original_ocr_engine:
        old_ocr_engine = _original_ocr_engine.get(instance.pk)
        if old_ocr_engine and old_ocr_engine != instance.ocr_engine:
            ocr_engine_changed = True
            logger.info(f"OCR engine changed from '{old_ocr_engine}' to '{instance.ocr_engine}' for document {instance.id} - will reprocess")
        # Clean up the tracking dict
        del _original_ocr_engine[instance.pk]
    
    # Process if:
    # 1. Document was just created (new document)
    # 2. File was changed (detected by checking if file path exists and pages don't match)
    # 3. OCR engine was changed (need to reprocess with new engine)
    if created or not has_pages or ocr_engine_changed:
        try:
            # Import here to avoid circular imports
            from .views import process_document_file
            
            # Delete existing pages if reprocessing (use transaction only for delete)
            if has_pages:
                with transaction.atomic():
                    instance.pages.all().delete()
            
            # Process the document (this may take a while for large files)
            # Don't wrap this in transaction.atomic() as it can cause SQLite locking issues
            # during long-running OCR operations. The process_document_file function
            # will handle its own database operations.
            process_document_file(instance)
            
            logger.info(f"Successfully processed document {instance.id} ({instance.title})")
        except Exception as e:
            logger.error(f"Error processing document {instance.id}: {str(e)}", exc_info=True)
            # Don't raise exception to avoid breaking the save operation
            # The error will be logged but document will still be saved


@receiver(pre_save, sender=Document)
def set_file_type_and_track_ocr_engine(sender, instance, **kwargs):
    """
    Automatically set file_type based on file extension, ensure OCR engine is set,
    and track OCR engine changes for reprocessing
    """
    # Track OCR engine change before save
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            _original_ocr_engine[instance.pk] = old_instance.ocr_engine
        except Document.DoesNotExist:
            _original_ocr_engine[instance.pk] = None
    
    # Set file_type if not already set
    if instance.file and not instance.file_type:
        filename = instance.file.name.lower()
        if filename.endswith('.pdf'):
            instance.file_type = 'pdf'
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            instance.file_type = 'image'
        else:
            instance.file_type = 'unknown'
    
    # Ensure OCR engine has a default value if not set
    if not instance.ocr_engine:
        instance.ocr_engine = 'mineru'

