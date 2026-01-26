from django import forms
from .models import Document, Prompt, Schema
import re
import json


class DocumentForm(forms.ModelForm):
    """Form for creating and updating documents"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'ocr_engine']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter document description (optional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg'
            }),
            'ocr_engine': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('mineru', 'MinerU (Default)'),
                ('pymupdf', 'PyMuPDF (PDF Text Extraction)'),
                ('pdfplumber', 'pdfplumber (PDF Text Extraction)'),
                ('tesseract', 'Tesseract OCR'),
                ('deepseek', 'DeepSeek OCR'),
                ('paddleocr', 'PaddleOCR'),
                ('trocr', 'TrOCR (Transformer OCR)'),
                ('donut', 'Donut (Document Understanding)'),
                ('olmocr', 'OLMOCR (AI-Powered OCR)'),
                ('lightonocr', 'LightOnOCR-2-1B'),
            ]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make file required only for new documents
        if not self.instance.pk:
            self.fields['file'].required = True
        else:
            self.fields['file'].required = False


class PromptForm(forms.ModelForm):
    """Form for creating and updating prompts"""
    
    class Meta:
        model = Prompt
        fields = ['name', 'title', 'description', 'category', 'template', 'is_active', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., document_summary'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name for the prompt'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of what this prompt does'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'style': 'font-family: monospace; font-size: 12px;',
                'placeholder': 'Enter prompt template. Use {variable_name} for variables.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_template(self):
        """Validate template and extract variables"""
        template = self.cleaned_data.get('template')
        if template:
            # Extract variables from template
            pattern = r'\{(\w+)\}'
            variables = list(dict.fromkeys(re.findall(pattern, template)))
            
            # Store variables in instance for later use
            if not hasattr(self, '_extracted_variables'):
                self._extracted_variables = variables
            else:
                self._extracted_variables = variables
        return template
    
    def save(self, commit=True):
        """Override save to auto-extract variables"""
        instance = super().save(commit=False)
        
        # Auto-extract variables from template
        if instance.template:
            pattern = r'\{(\w+)\}'
            variables = list(dict.fromkeys(re.findall(pattern, instance.template)))
            instance.variables = variables
        
        if commit:
            instance.save()
        return instance


class SchemaForm(forms.ModelForm):
    """Form for creating and updating schemas"""
    
    class Meta:
        model = Schema
        fields = ['name', 'title', 'description', 'category', 'schema', 'is_active', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., invoice_schema'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name for the schema'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of what this schema is used for'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'schema': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 20,
                'style': 'font-family: monospace; font-size: 12px;',
                'placeholder': 'Enter JSON schema definition in JSON Schema format'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_schema(self):
        """Validate schema is valid JSON"""
        schema_data = self.cleaned_data.get('schema')
        if schema_data:
            # If it's a string, try to parse it
            if isinstance(schema_data, str):
                try:
                    schema_data = json.loads(schema_data)
                except json.JSONDecodeError as e:
                    raise forms.ValidationError(f"Invalid JSON format: {str(e)}")
            
            # Validate it's a dictionary
            if not isinstance(schema_data, dict):
                raise forms.ValidationError("Schema must be a JSON object")
            
            # Basic JSON Schema validation (check for required top-level keys)
            if 'type' not in schema_data and 'properties' not in schema_data:
                # Not strictly required, but warn if neither is present
                pass
            
            return schema_data
        return schema_data
    
    def save(self, commit=True):
        """Override save to auto-extract properties"""
        instance = super().save(commit=False)
        
        # Auto-extract properties from schema
        if instance.schema:
            properties = instance.extract_properties()
            instance.properties = properties
        
        if commit:
            instance.save()
        return instance

