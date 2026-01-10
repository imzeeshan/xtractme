from django.db import models
from django.urls import reverse
from django.utils import timezone
import json


class Document(models.Model):
    """Model representing a document that can contain multiple pages"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, blank=True)  # pdf, image, etc.
    ocr_engine = models.CharField(max_length=50, default='mineru')  # mineru, tesseract, deepseek
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return self.title or f"Document {self.id}"
    
    def get_absolute_url(self):
        return reverse('document_detail', kwargs={'pk': self.pk})
    
    @property
    def total_pages(self):
        """Return the total number of pages in this document"""
        return self.pages.count()
    
    @property
    def total_text_length(self):
        """Return the total length of all text in all pages"""
        return sum(len(page.text or '') for page in self.pages.all())


class Page(models.Model):
    """Model representing a single page within a document"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    page_number = models.PositiveIntegerField()
    text = models.TextField(blank=True)
    json_data = models.JSONField(blank=True, null=True, help_text="Structured JSON data from MinerU")
    image = models.ImageField(upload_to='pages/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page_number']
        unique_together = ['document', 'page_number']
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
    
    def __str__(self):
        return f"Page {self.page_number} of {self.document.title}"
    
    def get_absolute_url(self):
        return reverse('document_detail', kwargs={'pk': self.document.pk})
    
    def get_json_preview(self):
        """Return formatted JSON string for display"""
        if self.json_data:
            # Format JSON with proper indentation (4 spaces for better readability)
            formatted = json.dumps(self.json_data, indent=4, ensure_ascii=False, sort_keys=False)
            return formatted
        return None
    
    def get_page_pdf_url(self):
        """Generate URL to view this specific page from the PDF"""
        return reverse('page_preview', kwargs={'pk': self.pk})
    
    def get_blocks(self):
        """Extract all blocks (paragraphs, headings, etc.) from MinerU JSON data"""
        if not self.json_data:
            return []
        
        blocks = []
        # MinerU structure: pages -> blocks
        if 'blocks' in self.json_data:
            blocks = self.json_data['blocks']
        elif 'pages' in self.json_data and isinstance(self.json_data['pages'], list):
            # If it's a pages array, get blocks from the current page
            for page in self.json_data['pages']:
                if page.get('page_number') == self.page_number and 'blocks' in page:
                    blocks = page['blocks']
                    break
        
        return blocks
    
    def get_tables(self):
        """Extract all tables from MinerU JSON data"""
        if not self.json_data:
            return []
        
        tables = []
        blocks = self.get_blocks()
        for block in blocks:
            if block.get('type') == 'table' or 'table' in block.get('type', '').lower():
                tables.append(block)
        
        return tables
    
    def get_formulas(self):
        """Extract all formulas/equations from MinerU JSON data"""
        if not self.json_data:
            return []
        
        formulas = []
        blocks = self.get_blocks()
        for block in blocks:
            if block.get('type') == 'formula' or 'formula' in block.get('type', '').lower():
                formulas.append(block)
        
        return formulas
    
    def get_headings(self):
        """Extract all headings from MinerU JSON data"""
        if not self.json_data:
            return []
        
        headings = []
        blocks = self.get_blocks()
        for block in blocks:
            block_type = block.get('type', '').lower()
            if 'heading' in block_type or 'title' in block_type or block.get('level'):
                headings.append(block)
        
        return headings
    
    def get_paragraphs(self):
        """Extract all paragraphs from MinerU JSON data"""
        if not self.json_data:
            return []
        
        paragraphs = []
        blocks = self.get_blocks()
        for block in blocks:
            block_type = block.get('type', '').lower()
            if 'paragraph' in block_type or 'text' in block_type:
                if block.get('type') != 'table' and 'formula' not in block_type:
                    paragraphs.append(block)
        
        return paragraphs
    
    def get_bounding_boxes(self):
        """Extract all bounding boxes from MinerU JSON data"""
        if not self.json_data:
            return []
        
        bboxes = []
        blocks = self.get_blocks()
        for block in blocks:
            if 'bbox' in block or 'bounding_box' in block:
                bbox = block.get('bbox') or block.get('bounding_box')
                if bbox:
                    bboxes.append({
                        'text': block.get('text', ''),
                        'type': block.get('type', 'unknown'),
                        'bbox': bbox
                    })
        
        return bboxes
    
    def get_layout_structure(self):
        """Get a structured representation of the page layout"""
        if not self.json_data:
            return None
        
        return {
            'page_number': self.page_number,
            'blocks_count': len(self.get_blocks()),
            'tables_count': len(self.get_tables()),
            'formulas_count': len(self.get_formulas()),
            'headings_count': len(self.get_headings()),
            'paragraphs_count': len(self.get_paragraphs()),
            'has_layout': bool(self.get_blocks()),
            'blocks': self.get_blocks()
        }
    
    def extract_text_by_type(self, block_type='paragraph'):
        """Extract text from blocks of a specific type"""
        if not self.json_data:
            return []
        
        texts = []
        blocks = self.get_blocks()
        for block in blocks:
            if block.get('type', '').lower() == block_type.lower():
                text = block.get('text', '')
                if text:
                    texts.append(text)
        
        return texts


class Prompt(models.Model):
    """Model for storing LLM prompt templates"""
    
    PROMPT_CATEGORIES = [
        ('document', 'Document'),
        ('page', 'Page'),
        ('structured', 'Structured Data'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the prompt (e.g., 'document_summary')"
    )
    title = models.CharField(
        max_length=255,
        help_text="Display name for the prompt"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this prompt does"
    )
    category = models.CharField(
        max_length=50,
        choices=PROMPT_CATEGORIES,
        default='document',
        help_text="Category of the prompt"
    )
    template = models.TextField(
        help_text="Prompt template with {variables} for formatting"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this prompt is active and available for use"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default prompt for its category"
    )
    variables = models.JSONField(
        default=list,
        blank=True,
        help_text="List of variable names used in the template (e.g., ['document_title', 'document_content'])"
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this prompt has been used"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_prompts',
        help_text="User who created this prompt"
    )
    
    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Prompt'
        verbose_name_plural = 'Prompts'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.name})"
    
    def get_absolute_url(self):
        return reverse('admin:core_prompt_change', args=[self.pk])
    
    def format(self, **kwargs) -> str:
        """Format the prompt template with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one default per category"""
        if self.is_default:
            # Set all other prompts in the same category to not default
            Prompt.objects.filter(
                category=self.category,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Schema(models.Model):
    """Model for storing JSON schema definitions"""
    
    SCHEMA_CATEGORIES = [
        ('document', 'Document'),
        ('page', 'Page'),
        ('structured', 'Structured Data'),
        ('extraction', 'Data Extraction'),
        ('validation', 'Validation'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the schema (e.g., 'invoice_schema')"
    )
    title = models.CharField(
        max_length=255,
        help_text="Display name for the schema"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this schema is used for"
    )
    category = models.CharField(
        max_length=50,
        choices=SCHEMA_CATEGORIES,
        default='structured',
        help_text="Category of the schema"
    )
    schema = models.JSONField(
        help_text="JSON schema definition (JSON Schema format)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this schema is active and available for use"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default schema for its category"
    )
    properties = models.JSONField(
        default=list,
        blank=True,
        help_text="List of property names extracted from the schema (e.g., ['invoice_number', 'total_amount'])"
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this schema has been used"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_schemas',
        help_text="User who created this schema"
    )
    
    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Schema'
        verbose_name_plural = 'Schemas'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.name})"
    
    def get_absolute_url(self):
        return reverse('admin:core_schema_change', args=[self.pk])
    
    def validate_data(self, data):
        """Validate data against the schema (requires jsonschema library)"""
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=self.schema)
            return True, None
        except ImportError:
            return False, "jsonschema library is not installed"
        except jsonschema.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def extract_properties(self):
        """Extract property names from the schema definition"""
        properties_list = []
        if isinstance(self.schema, dict):
            # Extract from properties if it's a JSON Schema object
            if 'properties' in self.schema:
                properties_list = list(self.schema['properties'].keys())
            # Also check for required fields
            if 'required' in self.schema:
                required = self.schema['required']
                for prop in required:
                    if prop not in properties_list:
                        properties_list.append(prop)
        return properties_list
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one default per category and extract properties"""
        if self.is_default:
            # Set all other schemas in the same category to not default
            Schema.objects.filter(
                category=self.category,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        # Extract properties from schema if not already set
        if self.schema and not self.properties:
            self.properties = self.extract_properties()
        
        super().save(*args, **kwargs)


class Settings(models.Model):
    """Application settings - singleton model (only one instance)"""
    
    OCR_ENGINE_CHOICES = [
        ('mineru', 'MinerU'),
        ('tesseract', 'Tesseract OCR'),
        ('deepseek', 'DeepSeek OCR'),
        ('paddleocr', 'PaddleOCR'),
        ('trocr', 'TrOCR'),
        ('donut', 'Donut'),
        ('olmocr', 'OLMOCR'),
    ]
    
    # Singleton identifier
    singleton_id = models.IntegerField(default=1, unique=True, editable=False)
    
    # Ollama LLM Settings
    ollama_model = models.CharField(
        max_length=100,
        default='qwen3:4b',
        help_text="Ollama model name (e.g., 'qwen3:4b', 'llama3.2')"
    )
    ollama_host = models.URLField(
        default='http://localhost:11434',
        help_text="Ollama server URL"
    )
    
    # OCR Settings
    default_ocr_engine = models.CharField(
        max_length=50,
        choices=OCR_ENGINE_CHOICES,
        default='mineru',
        help_text="Default OCR engine to use for document processing"
    )
    
    # DeepSeek OCR Settings
    deepseek_ocr_enabled = models.BooleanField(
        default=True,
        help_text="Enable DeepSeek OCR integration"
    )
    deepseek_ocr_api_url = models.URLField(
        default='http://localhost:8001',
        help_text="DeepSeek OCR API URL"
    )
    deepseek_ocr_use_api = models.BooleanField(
        default=True,
        help_text="Use DeepSeek OCR via API (if False, uses local installation)"
    )
    
    # OLMOCR Settings
    olmocr_enabled = models.BooleanField(
        default=True,
        help_text="Enable OLMOCR integration"
    )
    olmocr_api_url = models.URLField(
        default='https://api.olmocr.com',
        blank=True,
        help_text="OLMOCR API URL (only used if 'Use OLMOCR via API' is enabled)"
    )
    olmocr_use_api = models.BooleanField(
        default=False,
        help_text="Use OLMOCR via API (if False, uses local installation - requires pip install olmocr)"
    )
    
    # General Settings
    site_title = models.CharField(
        max_length=255,
        default='XtractMe',
        help_text="Site title displayed in admin interface"
    )
    site_header = models.CharField(
        max_length=255,
        default='XtractMe',
        help_text="Site header displayed in admin interface"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'
    
    def __str__(self):
        return 'Application Settings'
    
    def save(self, *args, **kwargs):
        """Ensure only one settings instance exists"""
        self.singleton_id = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(singleton_id=1)
        return settings
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of settings"""
        pass