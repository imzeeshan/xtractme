from django.contrib import admin
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from unfold.admin import ModelAdmin, StackedInline
from .models import Document, Page, Prompt, Schema, Settings
from .forms import PromptForm, SchemaForm
import fitz  # PyMuPDF
import base64
import json
import logging

logger = logging.getLogger(__name__)


class PageInline(StackedInline):
    """Inline admin for Pages within Document admin with side-by-side PDF and JSON preview"""
    model = Page
    extra = 0
    readonly_fields = ['page_number', 'pdf_json_preview', 'created_at', 'updated_at']
    fields = ['page_number', 'pdf_json_preview', 'text', 'image']
    can_delete = True
    show_change_link = True
    # Remove collapse class so pages are visible by default
    # classes = ['collapse']  # Uncomment to collapse by default
    
    class Media:
        css = {
            'all': ('admin/css/page_carousel.css',)
        }
        js = ('admin/js/page_carousel.js',)
    
    def pdf_json_preview(self, obj):
        """Display PDF page preview and JSON side-by-side"""
        if not obj or not obj.pk:
            return mark_safe('<p style="color: #999; padding: 20px;">Save the page first to see preview</p>')
        
        try:
            document = obj.document
            if not document.file:
                return mark_safe('<p style="color: #999; padding: 20px;">No document file available</p>')
            
            if document.file_type != 'pdf':
                return mark_safe('<p style="color: #999; padding: 20px;">PDF preview only available for PDF documents</p>')
            
            # Check if file exists
            import os
            if not os.path.exists(document.file.path):
                return mark_safe('<p style="color: red; padding: 20px;">PDF file not found on disk</p>')
            
            # Generate PDF page preview
            pdf_preview_html = mark_safe('<p style="color: #999;">Loading preview...</p>')
            try:
                doc = fitz.open(document.file.path)
                if obj.page_number <= len(doc):
                    pdf_page = doc.load_page(obj.page_number - 1)  # page_number is 1-indexed
                    pix = pdf_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x resolution
                    img_bytes = pix.tobytes("png")
                    pdf_preview_data = base64.b64encode(img_bytes).decode('utf-8')
                    pdf_preview_html = format_html(
                        '<img src="data:image/png;base64,{}" style="max-width: 100%; width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; display: block;" alt="Page {}">',
                        pdf_preview_data, obj.page_number
                    )
                else:
                    pdf_preview_html = format_html('<p style="color: red;">Page {} does not exist (PDF has {} pages)</p>', obj.page_number, len(doc))
                doc.close()
            except Exception as e:
                logger.error(f"Error generating PDF preview for page {obj.pk}: {str(e)}", exc_info=True)
                pdf_preview_html = format_html('<p style="color: red;">Error loading PDF preview: {}</p>', str(e))
            
            # Generate JSON preview
            json_preview_html = mark_safe('<p style="color: #999;">No JSON data available</p>')
            if obj.json_data:
                try:
                    json_str = json.dumps(obj.json_data, indent=2, ensure_ascii=False)
                    escaped_json = escape(json_str)
                    json_preview_html = format_html(
                        '<div style="background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 12px; max-height: 600px; overflow-y: auto; font-family: monospace; font-size: 12px; width: 100%; box-sizing: border-box;"><pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">{}</pre></div>',
                        escaped_json
                    )
                except Exception as e:
                    json_preview_html = format_html('<p style="color: red;">Error formatting JSON: {}</p>', str(e))
            
            # Return side-by-side layout with carousel support - optimized for maximum space usage
            # Use mark_safe since pdf_preview_html and json_preview_html are already SafeString objects
            page_num = obj.page_number if obj else 0
            return mark_safe(f'''
                <div class="page-preview-carousel-item" data-page-number="{page_num}">
                    <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 25px; margin: 10px 0; padding: 20px; background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; width: 100%; box-sizing: border-box;">
                        <div style="display: flex; flex-direction: column; width: 100%;">
                            <h4 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #333;">PDF Page Preview</h4>
                            <div style="background: white; padding: 12px; border-radius: 4px; border: 1px solid #ddd; width: 100%; box-sizing: border-box;">
                                {pdf_preview_html}
                            </div>
                        </div>
                        <div style="display: flex; flex-direction: column; width: 100%;">
                            <h4 style="margin: 0 0 12px 0; font-size: 15px; font-weight: 600; color: #333;">JSON Data</h4>
                            <div style="width: 100%; box-sizing: border-box;">
                                {json_preview_html}
                            </div>
                        </div>
                    </div>
                </div>
            ''')
        except Exception as e:
            logger.error(f"Error in pdf_json_preview for page {obj.pk if obj else 'None'}: {str(e)}", exc_info=True)
            return format_html('<p style="color: red;">Error: {}</p>', str(e))
    
    pdf_json_preview.short_description = 'PDF & JSON Preview'
    
    def get_queryset(self, request):
        """Override to ensure pages are ordered by page_number"""
        qs = super().get_queryset(request)
        return qs.order_by('page_number')


class DocumentAdminForm(forms.ModelForm):
    """Custom form for Document admin with OCR engine dropdown"""
    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'ocr_engine': forms.Select(choices=[
                ('mineru', 'MinerU (Default)'),
                ('pymupdf', 'PyMuPDF (PDF Text Extraction)'),
                ('pdfplumber', 'pdfplumber (PDF Text Extraction)'),
                ('tesseract', 'Tesseract OCR'),
                ('deepseek', 'DeepSeek OCR'),
                ('paddleocr', 'PaddleOCR'),
                ('trocr', 'TrOCR (Transformer OCR)'),
                ('donut', 'Donut (Document Understanding)'),
                ('olmocr', 'OLMOCR (AI-Powered OCR)'),
            ]),
        }


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    """Admin interface for Document model"""
    icon = "article"
    form = DocumentAdminForm
    list_display = ['title', 'file_type', 'ocr_engine', 'total_pages', 'created_at', 'updated_at', 'send_to_llm_button']
    list_filter = ['file_type', 'ocr_engine', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'total_pages', 'total_text_length']
    actions = ['reprocess_documents']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('File Information', {
            'fields': ('file', 'file_type', 'ocr_engine')
        }),
        ('Statistics', {
            'fields': ('total_pages', 'total_text_length', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [PageInline]
    
    class Media:
        css = {
            'all': ('admin/css/page_carousel.css',)
        }
        js = ('admin/js/page_carousel.js', 'admin/js/send_to_llm.js',)
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure file_type and ocr_engine are set before saving"""
        # Set file_type if not already set
        if obj.file and not obj.file_type:
            filename = obj.file.name.lower()
            if filename.endswith('.pdf'):
                obj.file_type = 'pdf'
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                obj.file_type = 'image'
            else:
                obj.file_type = 'unknown'
        
        # Ensure ocr_engine has a valid default if not set
        if not obj.ocr_engine:
            obj.ocr_engine = 'mineru'
        
        # Save the model (signals will handle processing)
        super().save_model(request, obj, form, change)
        
        # Show message about processing
        if obj.file:
            if obj.pages.exists():
                messages.success(request, f'Document "{obj.title}" saved and processed successfully. {obj.total_pages} pages extracted.')
            else:
                messages.warning(request, f'Document "{obj.title}" saved, but processing may still be in progress or failed. Check pages.')
    
    def send_to_llm_button(self, obj):
        """Display a button to send document to LLM"""
        if not obj.pk:
            return "-"
        
        button_html = format_html(
            '<a href="#" class="button send-to-llm-btn" data-document-id="{}" style="padding: 5px 10px; background: #417690; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">Send to LLM</a>',
            obj.pk
        )
        return button_html
    
    send_to_llm_button.short_description = "Send to LLM"
    
    def reprocess_documents(self, request, queryset):
        """Admin action to reprocess selected documents"""
        from .views import process_document_file
        
        processed = 0
        failed = 0
        
        for document in queryset:
            if not document.file:
                continue
            try:
                # Delete existing pages
                document.pages.all().delete()
                # Reprocess
                process_document_file(document)
                processed += 1
            except Exception as e:
                failed += 1
                self.message_user(request, f'Error processing "{document.title}": {str(e)}', level=messages.ERROR)
        
        if processed > 0:
            self.message_user(request, f'Successfully reprocessed {processed} document(s).', level=messages.SUCCESS)
        if failed > 0:
            self.message_user(request, f'Failed to process {failed} document(s).', level=messages.WARNING)
    
    reprocess_documents.short_description = "Reprocess selected documents (extract pages)"
    
    def get_urls(self):
        """Add custom URLs for Document admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/send-to-llm/',
                self.admin_site.admin_view(self.send_to_llm_view),
                name='core_document_send_to_llm',
            ),
            path(
                '<path:object_id>/llm-options/',
                self.admin_site.admin_view(self.llm_options_view),
                name='core_document_llm_options',
            ),
        ]
        return custom_urls + urls
    
    def llm_options_view(self, request, object_id):
        """Get available prompts, schemas, and pages for LLM"""
        from django.shortcuts import get_object_or_404
        
        document = get_object_or_404(Document, pk=object_id)
        
        # Get only active prompts from database (exclude built-in prompts)
        prompts = {}
        try:
            from .models import Prompt
            from .prompts import PromptManager
            db_prompts = Prompt.objects.filter(is_active=True).order_by('category', 'title')
            for db_prompt in db_prompts:
                # Use title as display name, fallback to description, then formatted name
                display_name = db_prompt.title or db_prompt.description or PromptManager._format_prompt_name(db_prompt.name)
                prompts[db_prompt.name] = display_name
        except Exception as e:
            # If database is not available or model doesn't exist, return empty
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error fetching database prompts: {str(e)}")
        
        # Get active schemas from database
        schemas = {}
        try:
            from .models import Schema
            db_schemas = Schema.objects.filter(is_active=True).order_by('category', 'title')
            for db_schema in db_schemas:
                # Use title as display name, fallback to name
                display_name = db_schema.title or db_schema.name
                schemas[str(db_schema.id)] = display_name
        except Exception as e:
            # If database is not available or model doesn't exist, return empty
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error fetching database schemas: {str(e)}")
        
        # Get pages with preview
        pages = []
        for page in document.pages.order_by('page_number'):
            pages.append({
                'id': page.id,
                'page_number': page.page_number,
                'text_preview': (page.text[:100] + '...') if page.text and len(page.text) > 100 else (page.text or '')
            })
        
        return JsonResponse({
            'success': True,
            'prompts': prompts,
            'schemas': schemas,
            'pages': pages
        })
    
    def send_to_llm_view(self, request, object_id):
        """Send document pages to Ollama LLM"""
        from django.shortcuts import get_object_or_404
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method allowed'}, status=405)
        
        document = get_object_or_404(Document, pk=object_id)
        
        # Check if document has pages
        if not document.pages.exists():
            return JsonResponse({
                'success': False,
                'error': 'Document has no pages to send. Please process the document first.'
            }, status=400)
        
        try:
            # Try to import ollama
            try:
                import ollama
            except ImportError:
                return JsonResponse({
                    'success': False,
                    'error': 'Ollama package is not installed. Please install it with: pip install ollama'
                }, status=500)
            
            # Get Ollama settings from Django settings
            ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')  # Default model
            ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')  # Default Ollama host
            
            # Get selected pages from request
            selected_page_ids = request.POST.getlist('selected_pages', [])
            
            # Collect selected page texts (or all pages if none selected)
            pages_data = []
            if selected_page_ids:
                # Get only selected pages
                selected_pages = document.pages.filter(id__in=selected_page_ids).order_by('page_number')
            else:
                # If no pages selected, use all pages
                selected_pages = document.pages.order_by('page_number')
            
            for page in selected_pages:
                page_text = page.text or ''
                if page_text.strip():
                    pages_data.append({
                        'page_number': page.page_number,
                        'text': page_text
                    })
            
            if not pages_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No text content found in selected pages.'
                }, status=400)
            
            # Use the prompts module to generate the prompt
            from .prompts import PromptManager
            from .models import Schema
            import json
            
            # Get prompt type from request (default to document_summary)
            prompt_type = request.POST.get('prompt_type', 'document_summary')
            
            # Get schema_id from request (optional)
            schema_id = request.POST.get('schema_id', '')
            schema_data = None
            schema_name = None
            
            if schema_id:
                try:
                    schema = Schema.objects.get(pk=schema_id, is_active=True)
                    schema_data = schema.schema
                    schema_name = schema.title or schema.name
                    logger.info(f"Using schema: {schema_name} (ID: {schema_id})")
                except Schema.DoesNotExist:
                    logger.warning(f"Schema with ID {schema_id} not found or inactive, proceeding without schema")
                except Exception as e:
                    logger.warning(f"Error fetching schema: {str(e)}, proceeding without schema")
            
            # Get available prompts (check both database and built-in)
            available_prompts = PromptManager.list_prompts(include_database=True)
            
            # Validate prompt type - check if it exists in available prompts
            if prompt_type not in available_prompts:
                logger.warning(f"Invalid prompt type '{prompt_type}', using default 'document_summary'")
                prompt_type = 'document_summary'
            
            # Format the prompt using the PromptManager (will check database first, then built-in)
            try:
                prompt = PromptManager.format_document_prompt(
                    prompt_name=prompt_type,
                    document_title=document.title,
                    pages_data=pages_data,
                    use_database=True  # Check database first
                )
                
                # If a schema is provided, append schema instructions to the prompt
                if schema_data:
                    schema_instructions = "\n\n=== IMPORTANT: SCHEMA-BASED EXTRACTION ===\n"
                    schema_instructions += f"You must extract and structure the information according to the following JSON schema: {schema_name}\n\n"
                    schema_instructions += "SCHEMA DEFINITION:\n"
                    schema_instructions += json.dumps(schema_data, indent=2)
                    schema_instructions += "\n\n"
                    schema_instructions += "INSTRUCTIONS:\n"
                    schema_instructions += "1. Extract all relevant information from the document that matches the schema structure.\n"
                    schema_instructions += "2. Structure your response as a valid JSON object that conforms to the schema above.\n"
                    schema_instructions += "3. Include all required fields as specified in the schema.\n"
                    schema_instructions += "4. Use null for optional fields that are not found in the document.\n"
                    schema_instructions += "5. Ensure all data types match the schema (strings, numbers, dates, etc.).\n"
                    schema_instructions += "6. Return ONLY the JSON object, without any additional explanation or markdown formatting.\n"
                    schema_instructions += "\nYour response must be valid JSON that can be validated against the provided schema.\n"
                    
                    prompt += schema_instructions
                    
            except ValueError as e:
                logger.error(f"Error formatting prompt: {str(e)}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': f'Error formatting prompt: {str(e)}'
                }, status=500)
            
            # Send to Ollama
            try:
                # Close database connection before long-running LLM request
                # This prevents SQLite locking issues
                from django.db import connection
                connection.close()
                
                # Check if Ollama is accessible
                response = ollama.chat(
                    model=ollama_model,
                    messages=[
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                )
                
                # Extract the response
                llm_response = response.get('message', {}).get('content', '')
                
                # Save the LLM response to the document's description field
                # Re-fetch document to ensure we have a fresh connection
                document.refresh_from_db()
                document.description = llm_response
                document.save(update_fields=['description'])
                
                response_data = {
                    'success': True,
                    'response': llm_response,
                    'pages_sent': len(pages_data),
                    'model': ollama_model,
                    'prompt_name': prompt_type,
                    'saved_to_description': True
                }
                
                # Include schema information if used
                if schema_name:
                    response_data['schema_name'] = schema_name
                    response_data['schema_id'] = schema_id
                
                return JsonResponse(response_data)
                
            except Exception as e:
                logger.error(f"Error communicating with Ollama: {str(e)}", exc_info=True)
                error_msg = str(e)
                if 'Connection' in error_msg or 'connect' in error_msg.lower():
                    error_msg = f"Could not connect to Ollama at {ollama_host}. Please ensure Ollama is running."
                return JsonResponse({
                    'success': False,
                    'error': f'Error communicating with Ollama: {error_msg}'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error sending document to LLM: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }, status=500)


@admin.register(Page)
class PageAdmin(ModelAdmin):
    """Admin interface for Page model"""
    icon = "insert_drive_file"
    list_display = ['document', 'page_number', 'text_preview', 'has_json', 'created_at']
    list_filter = ['document', 'created_at']
    search_fields = ['document__title', 'text']
    readonly_fields = ['created_at', 'updated_at', 'json_preview']
    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'page_number')
        }),
        ('Content', {
            'fields': ('text', 'image')
        }),
        ('MinerU JSON Data', {
            'fields': ('json_data', 'json_preview'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show a preview of the page text"""
        if obj.text:
            return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
        return 'No text'
    text_preview.short_description = 'Text Preview'
    
    def has_json(self, obj):
        """Check if page has JSON data"""
        return bool(obj.json_data)
    has_json.boolean = True
    has_json.short_description = 'Has JSON'
    
    def json_preview(self, obj):
        """Show formatted JSON preview"""
        if obj.json_data:
            import json
            json_str = json.dumps(obj.json_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', json_str)
        return "No JSON data"
    json_preview.short_description = 'JSON Preview'


@admin.register(Prompt)
class PromptAdmin(ModelAdmin):
    """Admin interface for Prompt model"""
    icon = "psychology"
    form = PromptForm
    list_display = ['title', 'name', 'category', 'is_active', 'is_default', 'usage_count', 'created_at', 'preview_button']
    list_filter = ['category', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'title', 'description', 'template']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'description', 'category')
        }),
        ('Template', {
            'fields': ('template',),
            'description': 'Enter the prompt template. Use {variable_name} for variables that will be replaced when formatting.'
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default'),
            'description': 'Active prompts are available for use. Only one prompt per category can be set as default.'
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically add preview fieldsets only for existing objects"""
        fieldsets = list(super().get_fieldsets(request, obj))
        
        # Only add preview fieldsets if object exists
        if obj and obj.pk:
            fieldsets.insert(2, (
                'Preview', {
                    'fields': ('template_preview', 'variables_display'),
                    'classes': ('collapse',),
                    'description': 'Preview of the template and extracted variables'
                }
            ))
        
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """Dynamically add readonly fields based on object state"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # Only add preview methods if object exists
        if obj and obj.pk:
            readonly.extend(['template_preview', 'variables_display'])
        
        return readonly
    
    def template_preview(self, obj):
        """Show a preview of the template with syntax highlighting"""
        if not obj or not obj.pk:
            return ""
        
        if obj.template:
            # Escape HTML and show first 500 characters
            preview = escape(obj.template[:500])
            if len(obj.template) > 500:
                preview += '...'
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px;">{}</pre>',
                preview
            )
        return mark_safe('<div style="color: #999; font-style: italic;">No template</div>')
    template_preview.short_description = 'Template Preview'
    
    def variables_display(self, obj):
        """Display the variables used in the template"""
        if not obj or not obj.pk:
            return ""
        
        if obj.variables:
            variables_list = ', '.join([f'<code>{escape(v)}</code>' for v in obj.variables])
            return format_html('<div style="margin-top: 10px;">Variables: {}</div>', mark_safe(variables_list))
        return mark_safe('<div style="color: #999; font-style: italic;">No variables defined. Use {{variable_name}} in the template.</div>')
    variables_display.short_description = 'Template Variables'
    
    def preview_button(self, obj):
        """Button to preview the formatted prompt"""
        if obj.pk:
            return format_html(
                '<a href="#" class="button preview-prompt-btn" data-prompt-id="{}" style="padding: 5px 10px; background: #417690; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">Preview</a>',
                obj.pk
            )
        return "-"
    preview_button.short_description = "Preview"
    
    def save_model(self, request, obj, form, change):
        """Set created_by on first save and extract variables from template"""
        if not change:  # New object
            obj.created_by = request.user
        
        # Extract variables from template if template exists
        if obj.template:
            import re
            pattern = r'\{(\w+)\}'
            variables = list(dict.fromkeys(re.findall(pattern, obj.template)))
            obj.variables = variables
        
        super().save_model(request, obj, form, change)
    
    actions = ['activate_prompts', 'deactivate_prompts', 'reset_usage_count']
    
    def activate_prompts(self, request, queryset):
        """Activate selected prompts"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} prompt(s) activated.', messages.SUCCESS)
    activate_prompts.short_description = "Activate selected prompts"
    
    def deactivate_prompts(self, request, queryset):
        """Deactivate selected prompts"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} prompt(s) deactivated.', messages.SUCCESS)
    deactivate_prompts.short_description = "Deactivate selected prompts"
    
    def reset_usage_count(self, request, queryset):
        """Reset usage count for selected prompts"""
        count = queryset.update(usage_count=0)
        self.message_user(request, f'Usage count reset for {count} prompt(s).', messages.SUCCESS)
    reset_usage_count.short_description = "Reset usage count"
    
    def get_urls(self):
        """Add custom URLs for Prompt admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/preview/',
                self.admin_site.admin_view(self.preview_prompt_view),
                name='core_prompt_preview',
            ),
            path(
                '<path:object_id>/test-format/',
                self.admin_site.admin_view(self.test_format_view),
                name='core_prompt_test_format',
            ),
        ]
        return custom_urls + urls
    
    def preview_prompt_view(self, request, object_id):
        """Preview a prompt with sample data"""
        prompt = get_object_or_404(Prompt, pk=object_id)
        
        # Sample data for preview
        sample_data = {
            'document_title': 'Sample Document',
            'document_content': 'This is a sample document content for preview purposes.',
            'page_number': 1,
            'total_pages': 5,
            'question': 'What is this document about?',
        }
        
        try:
            formatted = prompt.format(**sample_data)
            return JsonResponse({
                'success': True,
                'formatted_prompt': formatted,
                'template': prompt.template,
                'variables': prompt.variables or []
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def test_format_view(self, request, object_id):
        """Test formatting a prompt with custom data"""
        from django.shortcuts import get_object_or_404
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method allowed'}, status=405)
        
        prompt = get_object_or_404(Prompt, pk=object_id)
        
        try:
            import json
            data = json.loads(request.body)
            formatted = prompt.format(**data)
            
            # Increment usage count
            prompt.usage_count += 1
            prompt.save(update_fields=['usage_count'])
            
            return JsonResponse({
                'success': True,
                'formatted_prompt': formatted
            })
        except (ValueError, KeyError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Error formatting prompt: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Error testing prompt format: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }, status=500)


@admin.register(Schema)
class SchemaAdmin(ModelAdmin):
    """Admin interface for Schema model"""
    icon = "code"
    form = SchemaForm
    list_display = ['title', 'name', 'category', 'is_active', 'is_default', 'usage_count', 'created_at', 'preview_button']
    list_filter = ['category', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'description', 'category')
        }),
        ('Schema Definition', {
            'fields': ('schema',),
            'description': 'Enter the JSON schema definition in JSON Schema format.'
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default'),
            'description': 'Active schemas are available for use. Only one schema per category can be set as default.'
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """Dynamically add preview fieldsets only for existing objects"""
        fieldsets = list(super().get_fieldsets(request, obj))
        
        # Only add preview fieldsets if object exists
        if obj and obj.pk:
            fieldsets.insert(2, (
                'Preview', {
                    'fields': ('schema_preview', 'properties_display'),
                    'classes': ('collapse',),
                    'description': 'Preview of the schema and extracted properties'
                }
            ))
        
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """Dynamically add readonly fields based on object state"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # Only add preview methods if object exists
        if obj and obj.pk:
            readonly.extend(['schema_preview', 'properties_display'])
        
        return readonly
    
    def schema_preview(self, obj):
        """Show a preview of the schema with syntax highlighting"""
        if not obj or not obj.pk:
            return ""
        
        if obj.schema:
            try:
                # Format JSON with proper indentation
                schema_json = json.dumps(obj.schema, indent=2, ensure_ascii=False)
                # Escape HTML
                preview = escape(schema_json)
                # Limit preview length
                if len(schema_json) > 1000:
                    preview = escape(schema_json[:1000]) + '...'
                return format_html(
                    '<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px;">{}</pre>',
                    preview
                )
            except Exception as e:
                return mark_safe(f'<div style="color: #999; font-style: italic;">Error displaying schema: {str(e)}</div>')
        return mark_safe('<div style="color: #999; font-style: italic;">No schema</div>')
    schema_preview.short_description = 'Schema Preview'
    
    def properties_display(self, obj):
        """Display the properties extracted from the schema"""
        if not obj or not obj.pk:
            return ""
        
        if obj.properties:
            properties_list = ', '.join([f'<code>{escape(p)}</code>' for p in obj.properties])
            return format_html('<div style="margin-top: 10px;">Properties: {}</div>', mark_safe(properties_list))
        return mark_safe('<div style="color: #999; font-style: italic;">No properties extracted. Add a "properties" field to your JSON schema.</div>')
    properties_display.short_description = 'Schema Properties'
    
    def preview_button(self, obj):
        """Button to preview the schema"""
        if obj.pk:
            return format_html(
                '<a href="#" class="button preview-schema-btn" data-schema-id="{}" style="padding: 5px 10px; background: #417690; color: white; text-decoration: none; border-radius: 3px; font-size: 11px;">Preview</a>',
                obj.pk
            )
        return "-"
    preview_button.short_description = "Preview"
    
    def save_model(self, request, obj, form, change):
        """Set created_by on first save and extract properties from schema"""
        if not change:  # New object
            obj.created_by = request.user
        
        # Extract properties from schema if schema exists
        if obj.schema:
            properties = obj.extract_properties()
            obj.properties = properties
        
        super().save_model(request, obj, form, change)
    
    actions = ['activate_schemas', 'deactivate_schemas', 'reset_usage_count']
    
    def activate_schemas(self, request, queryset):
        """Activate selected schemas"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} schema(s) activated.', messages.SUCCESS)
    activate_schemas.short_description = "Activate selected schemas"
    
    def deactivate_schemas(self, request, queryset):
        """Deactivate selected schemas"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} schema(s) deactivated.', messages.SUCCESS)
    deactivate_schemas.short_description = "Deactivate selected schemas"
    
    def reset_usage_count(self, request, queryset):
        """Reset usage count for selected schemas"""
        count = queryset.update(usage_count=0)
        self.message_user(request, f'Usage count reset for {count} schema(s).', messages.SUCCESS)
    reset_usage_count.short_description = "Reset usage count"
    
    def get_urls(self):
        """Add custom URLs for Schema admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/preview/',
                self.admin_site.admin_view(self.preview_schema_view),
                name='core_schema_preview',
            ),
            path(
                '<path:object_id>/validate/',
                self.admin_site.admin_view(self.validate_data_view),
                name='core_schema_validate',
            ),
        ]
        return custom_urls + urls
    
    def preview_schema_view(self, request, object_id):
        """Preview a schema"""
        from django.shortcuts import get_object_or_404
        schema = get_object_or_404(Schema, pk=object_id)
        
        try:
            schema_json = json.dumps(schema.schema, indent=2, ensure_ascii=False)
            return JsonResponse({
                'success': True,
                'schema': schema.schema,
                'schema_json': schema_json,
                'properties': schema.properties or []
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def validate_data_view(self, request, object_id):
        """Validate data against the schema"""
        from django.shortcuts import get_object_or_404
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method allowed'}, status=405)
        
        schema = get_object_or_404(Schema, pk=object_id)
        
        try:
            data = json.loads(request.body)
            is_valid, error_message = schema.validate_data(data.get('data', {}))
            
            if is_valid:
                # Increment usage count
                schema.usage_count += 1
                schema.save(update_fields=['usage_count'])
                
                return JsonResponse({
                    'success': True,
                    'valid': True,
                    'message': 'Data is valid according to the schema'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'valid': False,
                    'error': error_message
                })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }, status=500)


@admin.register(Settings)
class SettingsAdmin(ModelAdmin):
    """Admin interface for Settings model (singleton)"""
    icon = "tune"
    
    def has_add_permission(self, request):
        """Only allow one settings instance"""
        try:
            return not Settings.objects.exists()
        except Exception:
            # Table doesn't exist yet, allow creation
            return True
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def has_module_permission(self, request):
        """Check if table exists before showing in admin"""
        try:
            # Try to check if table exists by attempting a query
            Settings.objects.exists()
            return True
        except Exception:
            # Table doesn't exist yet, hide from admin until migration is run
            return False
    
    list_display = ['__str__', 'ollama_model', 'ollama_host', 'default_ocr_engine', 'updated_at']
    readonly_fields = ['singleton_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Ollama LLM Settings', {
            'fields': ('ollama_model', 'ollama_host'),
            'description': 'Configure Ollama LLM integration settings. These settings are used when sending documents to LLM.'
        }),
        ('OCR Engine Settings', {
            'fields': ('default_ocr_engine',),
            'description': 'Select the default OCR engine to use for document processing.'
        }),
        ('DeepSeek OCR Settings', {
            'fields': ('deepseek_ocr_enabled', 'deepseek_ocr_api_url', 'deepseek_ocr_use_api'),
            'description': 'Configure DeepSeek OCR integration. Enable/disable and set API URL.'
        }),
        ('OLMOCR Settings', {
            'fields': ('olmocr_enabled', 'olmocr_use_api', 'olmocr_api_url'),
            'description': 'Configure OLMOCR integration. OLMOCR is an AI-powered OCR by Allen Institute for AI. Local mode (default) requires: pip install olmocr[gpu]. API mode uses online service.'
        }),
        ('General Settings', {
            'fields': ('site_title', 'site_header'),
            'description': 'General application settings displayed in the admin interface.'
        }),
        ('System Information', {
            'fields': ('singleton_id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'System information about this settings instance.'
        }),
    )
    
    def get_object(self, request, object_id=None, from_field=None):
        """Always return the singleton settings instance"""
        if object_id is None:
            object_id = 1
        try:
            return Settings.get_settings()
        except Exception:
            # Table doesn't exist or other error - create default settings
            try:
                return Settings.get_settings()
            except Exception:
                # If we still can't create, return None and let Django handle it
                return None
    
    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        """Override to always use singleton ID"""
        extra_context = extra_context or {}
        extra_context['title'] = 'Application Settings'
        extra_context['subtitle'] = 'Configure application-wide settings'
        return super().change_view(request, object_id='1', form_url=form_url, extra_context=extra_context)
    
    def changelist_view(self, request, extra_context=None):
        """Redirect changelist to change view for singleton"""
        from django.shortcuts import redirect
        return redirect('admin:core_settings_change', object_id=1)
