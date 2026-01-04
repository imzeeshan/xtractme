"""
Management command to reprocess documents and extract pages
Usage: python manage.py reprocess_documents [--all] [document_id ...]
"""
from django.core.management.base import BaseCommand
from core.models import Document
from core.views import process_document_file


class Command(BaseCommand):
    help = 'Reprocess documents to extract pages and JSON data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reprocess all documents',
        )
        parser.add_argument(
            'document_ids',
            nargs='*',
            type=int,
            help='Document IDs to reprocess',
        )

    def handle(self, *args, **options):
        if options['all']:
            documents = Document.objects.all()
            self.stdout.write(f'Reprocessing all {documents.count()} documents...')
        elif options['document_ids']:
            documents = Document.objects.filter(pk__in=options['document_ids'])
            self.stdout.write(f'Reprocessing {documents.count()} selected document(s)...')
        else:
            self.stdout.write(self.style.ERROR('Please specify --all or provide document IDs'))
            return

        processed = 0
        failed = 0

        for document in documents:
            if not document.file:
                self.stdout.write(
                    self.style.WARNING(f'Skipping "{document.title}" - no file attached')
                )
                continue

            try:
                self.stdout.write(f'Processing "{document.title}" (ID: {document.pk})...')
                
                # Check file exists
                import os
                if not document.file:
                    self.stdout.write(self.style.ERROR('  [ERROR] No file attached to document'))
                    failed += 1
                    continue
                
                file_path = document.file.path
                if not os.path.exists(file_path):
                    self.stdout.write(self.style.ERROR(f'  [ERROR] File not found: {file_path}'))
                    failed += 1
                    continue
                
                self.stdout.write(f'  File: {file_path}')
                self.stdout.write(f'  File type: {document.file_type}, OCR engine: {document.ocr_engine}')
                
                # Check PDF page count
                if document.file_type == 'pdf':
                    import fitz
                    try:
                        test_doc = fitz.open(file_path)
                        pdf_page_count = len(test_doc)
                        test_doc.close()
                        self.stdout.write(f'  PDF has {pdf_page_count} pages')
                        if pdf_page_count == 0:
                            self.stdout.write(self.style.WARNING('  [WARN] PDF has 0 pages'))
                            failed += 1
                            continue
                    except Exception as pdf_error:
                        self.stdout.write(self.style.ERROR(f'  [ERROR] Cannot open PDF: {str(pdf_error)}'))
                        failed += 1
                        continue
                
                # Delete existing pages
                page_count = document.pages.count()
                if page_count > 0:
                    document.pages.all().delete()
                    self.stdout.write(f'  Deleted {page_count} existing pages')
                
                # Process document
                self.stdout.write('  Running extraction...')
                process_document_file(document)
                
                # Check results
                new_page_count = document.pages.count()
                if new_page_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [OK] Successfully extracted {new_page_count} pages'
                        )
                    )
                    processed += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [WARN] No pages extracted (file may be empty or processing failed)'
                        )
                    )
                    failed += 1
                    
            except Exception as e:
                import traceback
                self.stdout.write(
                    self.style.ERROR(f'  [ERROR] Error processing "{document.title}": {str(e)}')
                )
                self.stdout.write(traceback.format_exc())
                failed += 1

        # Summary
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Successfully processed: {processed}'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed}'))
        self.stdout.write('=' * 50)

