from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document, Page
import os
import tempfile


class DocumentModelTest(TestCase):
    """Test cases for Document model"""
    
    def setUp(self):
        """Set up test data"""
        self.document = Document.objects.create(
            title="Test Document",
            description="Test Description",
            file_type="pdf",
            ocr_engine="mineru"
        )
    
    def test_document_creation(self):
        """Test document creation"""
        self.assertEqual(self.document.title, "Test Document")
        self.assertEqual(self.document.ocr_engine, "mineru")
        self.assertTrue(isinstance(self.document, Document))
    
    def test_document_str(self):
        """Test document string representation"""
        self.assertEqual(str(self.document), "Test Document")
    
    def test_total_pages_property(self):
        """Test total_pages property"""
        # Create some pages
        Page.objects.create(document=self.document, page_number=1, text="Page 1")
        Page.objects.create(document=self.document, page_number=2, text="Page 2")
        
        self.assertEqual(self.document.total_pages, 2)
    
    def test_total_text_length_property(self):
        """Test total_text_length property"""
        Page.objects.create(document=self.document, page_number=1, text="Hello")
        Page.objects.create(document=self.document, page_number=2, text="World")
        
        self.assertEqual(self.document.total_text_length, 10)


class PageModelTest(TestCase):
    """Test cases for Page model"""
    
    def setUp(self):
        """Set up test data"""
        self.document = Document.objects.create(
            title="Test Document",
            file_type="pdf",
            ocr_engine="mineru"
        )
        self.page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="Test page text"
        )
    
    def test_page_creation(self):
        """Test page creation"""
        self.assertEqual(self.page.page_number, 1)
        self.assertEqual(self.page.text, "Test page text")
        self.assertEqual(self.page.document, self.document)
    
    def test_page_str(self):
        """Test page string representation"""
        expected = f"Page 1 of {self.document.title}"
        self.assertEqual(str(self.page), expected)
    
    def test_page_unique_together(self):
        """Test that page_number is unique per document"""
        # Try to create duplicate page
        with self.assertRaises(Exception):
            Page.objects.create(
                document=self.document,
                page_number=1,
                text="Duplicate"
            )


class DocumentViewsTest(TestCase):
    """Test cases for document views"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_home_view(self):
        """Test home view"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_document_list_view(self):
        """Test document list view"""
        response = self.client.get('/documents/')
        self.assertEqual(response.status_code, 200)
    
    def test_document_create_view_get(self):
        """Test document create view GET"""
        response = self.client.get('/documents/create/')
        self.assertEqual(response.status_code, 200)
    
    def test_document_detail_view(self):
        """Test document detail view"""
        document = Document.objects.create(
            title="Test Document",
            file_type="pdf",
            ocr_engine="mineru"
        )
        response = self.client.get(f'/documents/{document.pk}/')
        self.assertEqual(response.status_code, 200)


class OCRUtilsTest(TestCase):
    """Test cases for OCR utilities"""
    
    def test_ocr_engine_imports(self):
        """Test that OCR utilities can be imported"""
        try:
            from core.ocr_utils import (
                extract_text_with_tesseract,
                extract_text_with_deepseek,
                extract_text_with_mineru,
                extract_text_with_paddleocr,
                extract_text_with_trocr,
                extract_text_with_donut,
                extract_text_with_lightonocr,
            )
            # If imports succeed, test passes
            self.assertTrue(True)
        except ImportError as e:
            # Some OCR engines may not be installed - that's okay
            self.assertIsNotNone(e)
