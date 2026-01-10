import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.db import transaction
from .models import Document, Page
from .forms import DocumentForm


def home(request):
    """Home page showing list of documents"""
    documents = Document.objects.all()[:6]  # Show only recent 6 documents
    return render(request, 'core/home.html', {'documents': documents})


def upload_file(request):
    """Legacy upload file view - redirects to document create"""
    from .ocr_utils import (
        extract_text_with_tesseract, 
        extract_text_with_deepseek, 
        extract_text_from_pdf,
        extract_text_with_mineru
    )
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        # Get the OCR engine from the form or default to mineru
        ocr_engine = request.POST.get('ocr_engine', 'mineru')
        
        try:
            # Check file type
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                if ocr_engine.lower() == 'mineru':
                    text = extract_text_with_mineru(file_path, file_type='image')
                elif ocr_engine.lower() == 'tesseract':
                    text = extract_text_with_tesseract(file_path)
                else:  # deepseek
                    text = extract_text_with_deepseek(file_path)
            elif filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(file_path, ocr_engine=ocr_engine)
            else:
                return JsonResponse({'error': 'Unsupported file format'}, status=400)
            
            return render(request, 'core/result.html', {
                'text': text,
                'filename': filename,
                'ocr_engine': ocr_engine
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return redirect('home')


def document_list(request):
    """List all documents"""
    documents = Document.objects.all()
    return render(request, 'core/document_list.html', {'documents': documents})


def document_detail(request, pk):
    """View details of a specific document"""
    document = get_object_or_404(Document, pk=pk)
    pages = document.pages.all()
    return render(request, 'core/document_detail.html', {
        'document': document,
        'pages': pages
    })


def page_preview(request, pk):
    """Preview a specific page with PDF and JSON"""
    page = get_object_or_404(Page, pk=pk)
    document = page.document
    
    # Get PDF page as image for preview
    import fitz
    from django.http import HttpResponse
    from django.conf import settings
    import base64
    from io import BytesIO
    
    pdf_preview_data = None
    try:
        if document.file_type == 'pdf':
            doc = fitz.open(document.file.path)
            if page.page_number <= len(doc):
                pdf_page = doc.load_page(page.page_number - 1)
                # Render page as image
                pix = pdf_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img_data = pix.tobytes("png")
                pdf_preview_data = base64.b64encode(img_data).decode('utf-8')
            doc.close()
    except Exception as e:
        pass
    
    # Get previous and next pages for navigation
    prev_page = document.pages.filter(page_number=page.page_number - 1).first()
    next_page = document.pages.filter(page_number=page.page_number + 1).first()
    
    return render(request, 'core/page_preview.html', {
        'page': page,
        'document': document,
        'pdf_preview_data': pdf_preview_data,
        'prev_page': prev_page,
        'next_page': next_page,
    })


def document_create(request):
    """Create a new document"""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            
            # Determine file type
            filename = document.file.name.lower()
            if filename.endswith('.pdf'):
                document.file_type = 'pdf'
            elif filename.endswith(('.png', '.jpg', '.jpeg')):
                document.file_type = 'image'
            else:
                document.file_type = 'unknown'
            
            document.save()
            
            # Process the file and create pages
            try:
                process_document_file(document)
                messages.success(request, f'Document "{document.title}" created successfully!')
                return redirect('document_detail', pk=document.pk)
            except Exception as e:
                messages.error(request, f'Error processing document: {str(e)}')
                document.delete()  # Clean up if processing fails
                return render(request, 'core/document_form.html', {'form': form})
    else:
        form = DocumentForm()
    
    return render(request, 'core/document_form.html', {
        'form': form,
        'title': 'Create Document'
    })


def document_update(request, pk):
    """Update an existing document"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            
            # If a new file was uploaded, reprocess it
            if 'file' in request.FILES:
                # Determine file type
                filename = document.file.name.lower()
                if filename.endswith('.pdf'):
                    document.file_type = 'pdf'
                elif filename.endswith(('.png', '.jpg', '.jpeg')):
                    document.file_type = 'image'
                else:
                    document.file_type = 'unknown'
                
                # Delete old pages
                document.pages.all().delete()
                
                # Process new file
                try:
                    process_document_file(document)
                except Exception as e:
                    messages.error(request, f'Error processing document: {str(e)}')
                    return render(request, 'core/document_form.html', {
                        'form': form,
                        'title': 'Update Document'
                    })
            
            document.save()
            messages.success(request, f'Document "{document.title}" updated successfully!')
            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(instance=document)
    
    return render(request, 'core/document_form.html', {
        'form': form,
        'document': document,
        'title': 'Update Document'
    })


def document_delete(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        title = document.title
        document.delete()
        messages.success(request, f'Document "{title}" deleted successfully!')
        return redirect('document_list')
    
    return render(request, 'core/document_confirm_delete.html', {'document': document})


def process_document_file(document):
    """Process uploaded file and create Page objects"""
    import fitz  # PyMuPDF
    from PIL import Image
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Import OCR utilities (may fail if dependencies not installed)
    try:
        from .ocr_utils import (
            extract_text_with_tesseract, 
            extract_text_with_deepseek,
            extract_text_with_deepseek_from_image,
            extract_text_with_mineru,
            extract_text_with_paddleocr,
            extract_text_with_trocr,
            extract_text_with_donut,
            extract_text_from_pdf,
            extract_pages_with_mineru_json,
            extract_pages_with_paddleocr_layout
        )
    except ImportError as e:
        logger.warning(f"Some OCR utilities not available: {str(e)}")
        # Define fallback functions
        def extract_text_with_tesseract(*args, **kwargs):
            return ""
        def extract_text_with_deepseek(*args, **kwargs):
            return ""
        def extract_text_with_deepseek_from_image(*args, **kwargs):
            return ""
        def extract_text_with_mineru(*args, **kwargs):
            return ""
        def extract_text_with_paddleocr(*args, **kwargs):
            return ""
        def extract_text_with_trocr(*args, **kwargs):
            return ""
        def extract_text_with_donut(*args, **kwargs):
            return ""
        def extract_text_from_pdf(*args, **kwargs):
            return ""
        def extract_pages_with_mineru_json(*args, **kwargs):
            return []
        def extract_pages_with_paddleocr_layout(*args, **kwargs):
            return []
    
    # Try to import pytesseract, but don't fail if not available
    try:
        import pytesseract
    except ImportError:
        pytesseract = None
        logger.warning("pytesseract not available - OCR will be limited")
    
    # Check if file exists
    if not document.file:
        raise ValueError(f"Document {document.id} has no file attached")
    
    file_path = document.file.path
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at path: {file_path}")
    
    # Auto-detect file type if not set
    if not document.file_type:
        filename = document.file.name.lower()
        if filename.endswith('.pdf'):
            document.file_type = 'pdf'
            document.save(update_fields=['file_type'])
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            document.file_type = 'image'
            document.save(update_fields=['file_type'])
        else:
            document.file_type = 'unknown'
            document.save(update_fields=['file_type'])
    
    # Validate and normalize OCR engine
    if not document.ocr_engine:
        logger.warning(f"Document {document.id} has no OCR engine set, defaulting to 'mineru'")
        document.ocr_engine = 'mineru'
        document.save(update_fields=['ocr_engine'])
    
    ocr_engine_lower = document.ocr_engine.lower()
    valid_engines = ['mineru', 'pymupdf', 'pdfplumber', 'tesseract', 'deepseek', 'paddleocr', 'trocr', 'donut', 'olmocr']
    if ocr_engine_lower not in valid_engines:
        logger.warning(f"Invalid OCR engine '{document.ocr_engine}' for document {document.id}, defaulting to 'mineru'")
        document.ocr_engine = 'mineru'
        document.save(update_fields=['ocr_engine'])
        ocr_engine_lower = 'mineru'
    
    logger.info(f"Processing document {document.id} ({document.title}): {file_path}")
    logger.info(f"File type: {document.file_type}, OCR engine: {document.ocr_engine} (normalized: '{ocr_engine_lower}')")
    
    if document.file_type == 'pdf':
        # If pdfplumber is selected, use it for PDF text extraction (best for PDFs with text layers)
        if ocr_engine_lower == 'pdfplumber':
            logger.info("Attempting pdfplumber text extraction...")
            from .ocr_utils import pdfplumber_available
            
            if not pdfplumber_available:
                logger.warning("pdfplumber not installed - falling back to traditional PDF processing")
                # Fall through to traditional processing
            else:
                try:
                    import pdfplumber
                    pages_created = 0
                    with pdfplumber.open(file_path) as pdf:
                        total_pages = len(pdf.pages)
                        logger.info(f"PDF has {total_pages} pages (pdfplumber)")
                        
                        for page_num, page in enumerate(pdf.pages, 1):
                            page_text = page.extract_text()
                            if page_text is None:
                                page_text = ""
                            
                            page_obj, created = Page.objects.get_or_create(
                                document=document,
                                page_number=page_num,
                                defaults={'text': page_text.strip()}
                            )
                            
                            if not created:
                                page_obj.text = page_text.strip()
                                page_obj.save()
                            
                            pages_created += 1
                            logger.info(f"{'Created' if created else 'Updated'} page {page_num} with pdfplumber (text length: {len(page_text)})")
                    
                    logger.info(f"Successfully processed {pages_created} pages with pdfplumber")
                    if pages_created == 0:
                        raise ValueError("Failed to extract any pages with pdfplumber")
                    return
                except Exception as e:
                    logger.error(f"Error with pdfplumber: {str(e)}", exc_info=True)
                    raise
        
        # If PyMuPDF is selected, use it for direct PDF text extraction
        if ocr_engine_lower == 'pymupdf':
            logger.info("Attempting PyMuPDF text extraction...")
            try:
                pages_created = 0
                doc = fitz.open(file_path)
                total_pages = len(doc)
                logger.info(f"PDF has {total_pages} pages (PyMuPDF)")
                
                if total_pages == 0:
                    doc.close()
                    raise ValueError("PDF file has no pages")
                
                for page_num in range(total_pages):
                    page = doc.load_page(page_num)
                    # Extract text directly using PyMuPDF (no OCR fallback)
                    page_text = page.get_text()
                    if page_text is None:
                        page_text = ""
                    
                    page_obj, created = Page.objects.get_or_create(
                        document=document,
                        page_number=page_num + 1,
                        defaults={'text': page_text.strip()}
                    )
                    
                    if not created:
                        page_obj.text = page_text.strip()
                        page_obj.save()
                    
                    pages_created += 1
                    logger.info(f"{'Created' if created else 'Updated'} page {page_num + 1} with PyMuPDF (text length: {len(page_text)})")
                
                doc.close()
                logger.info(f"Successfully processed {pages_created} pages with PyMuPDF")
                if pages_created == 0:
                    raise ValueError("Failed to extract any pages with PyMuPDF")
                return
            except Exception as e:
                logger.error(f"Error with PyMuPDF: {str(e)}", exc_info=True)
                raise
        
        # If MinerU is selected, use it for full PDF processing with JSON extraction
        if ocr_engine_lower == 'mineru':
            logger.info("Attempting MinerU JSON extraction...")
            # Use MinerU to extract page-by-page JSON data
            pages_data = extract_pages_with_mineru_json(file_path)
            
            if pages_data:
                # MinerU successfully extracted data
                logger.info(f"MinerU extracted {len(pages_data)} pages")
                
                # Create Page objects with JSON data
                for page_info in pages_data:
                    page_obj, created = Page.objects.get_or_create(
                        document=document,
                        page_number=page_info['page_number'],
                        defaults={
                            'text': page_info.get('text', ''),
                            'json_data': page_info.get('json_data', {})
                        }
                    )
                    if not created:
                        page_obj.text = page_info.get('text', '')
                        page_obj.json_data = page_info.get('json_data', {})
                        page_obj.save()
                
                logger.info(f"Successfully created/updated {len(pages_data)} page objects with MinerU")
                return
            else:
                # MinerU not available or returned no data - fall through to traditional method
                logger.info("MinerU not available or returned no data. Falling back to traditional PDF processing.")
                # Fall through to traditional processing
        
        # If OLMOCR is selected, use it for full PDF processing with JSON extraction
        if ocr_engine_lower == 'olmocr':
            logger.info("Attempting OLMOCR JSON extraction...")
            from .ocr_utils import extract_pages_with_olmocr_json, extract_text_with_olmocr, olmocr_available
            
            if olmocr_available:
                try:
                    # Use OLMOCR to extract page-by-page JSON data
                    pages_data = extract_pages_with_olmocr_json(file_path)
                    
                    # Check if we got any actual text content
                    has_content = any(page_info.get('text', '').strip() for page_info in pages_data) if pages_data else False
                    
                    if pages_data and has_content:
                        # OLMOCR successfully extracted data with content
                        logger.info(f"OLMOCR extracted {len(pages_data)} pages with JSON and text content")
                        
                        # Create Page objects with JSON data
                        for page_info in pages_data:
                            page_obj, created = Page.objects.get_or_create(
                                document=document,
                                page_number=page_info['page_number'],
                                defaults={
                                    'text': page_info.get('text', ''),
                                    'json_data': page_info.get('json_data', {})
                                }
                            )
                            if not created:
                                page_obj.text = page_info.get('text', '')
                                page_obj.json_data = page_info.get('json_data', {})
                                page_obj.save()
                        
                        logger.info(f"Successfully created/updated {len(pages_data)} page objects with OLMOCR JSON")
                        return
                    elif pages_data and not has_content:
                        # OLMOCR ran but produced no text - try fallback extraction
                        logger.warning("OLMOCR JSON extraction produced pages but no text content. Trying fallback text extraction...")
                        try:
                            # Try simple text extraction as fallback
                            full_text = extract_text_with_olmocr(file_path, file_type='pdf')
                            if full_text and not full_text.startswith("Error") and full_text.strip():
                                logger.info("OLMOCR fallback text extraction succeeded, updating pages...")
                                # Update pages with extracted text
                                for page_info in pages_data:
                                    page_obj, created = Page.objects.get_or_create(
                                        document=document,
                                        page_number=page_info['page_number'],
                                        defaults={'text': '', 'json_data': page_info.get('json_data', {})}
                                    )
                                    # Update JSON data with extracted text if available
                                    if page_info.get('json_data'):
                                        page_info['json_data']['text'] = full_text[:len(full_text)//len(pages_data)] if pages_data else ''
                                    if not created:
                                        page_obj.json_data = page_info.get('json_data', {})
                                        page_obj.save()
                                logger.info("Updated pages with fallback text extraction")
                                return
                        except Exception as fallback_error:
                            logger.error(f"OLMOCR fallback extraction also failed: {str(fallback_error)}")
                        
                        logger.warning("OLMOCR produced pages but no text content - falling back to traditional processing")
                        # Fall through to traditional processing
                    else:
                        logger.warning("OLMOCR returned no page data - falling back to traditional processing")
                        # Fall through to traditional processing
                except Exception as e:
                    logger.error(f"Error with OLMOCR: {str(e)}", exc_info=True)
                    # Fall through to traditional processing
            else:
                logger.warning("OLMOCR not available - falling back to traditional PDF processing")
                # Fall through to traditional processing
        
        # If PaddleOCR is selected, use enhanced layout extraction
        if ocr_engine_lower == 'paddleocr':
            logger.info("Attempting PaddleOCR layout extraction...")
            # Use PaddleOCR to extract page-by-page data with layout
            pages_data = extract_pages_with_paddleocr_layout(file_path)
            
            if pages_data:
                # PaddleOCR successfully extracted data with layout
                logger.info(f"PaddleOCR extracted {len(pages_data)} pages with layout")
                
                # Create Page objects with JSON data
                for page_info in pages_data:
                    page_obj, created = Page.objects.get_or_create(
                        document=document,
                        page_number=page_info['page_number'],
                        defaults={
                            'text': page_info.get('text', ''),
                            'json_data': page_info.get('json_data', {})
                        }
                    )
                    if not created:
                        page_obj.text = page_info.get('text', '')
                        page_obj.json_data = page_info.get('json_data', {})
                        page_obj.save()
                
                logger.info(f"Successfully created/updated {len(pages_data)} page objects with PaddleOCR layout")
                return
            else:
                # PaddleOCR layout extraction not available - fall through to traditional method
                logger.info("PaddleOCR layout extraction not available. Falling back to traditional PDF processing.")
                # Fall through to traditional processing
        
        # Traditional PDF processing method
        logger.info("Using traditional PDF processing method...")
        doc = fitz.open(file_path)
        total_pages = len(doc)
        logger.info(f"PDF has {total_pages} pages")
        
        if total_pages == 0:
            doc.close()
            raise ValueError("PDF file has no pages")
        
        pages_created = 0
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # Try to extract text directly first (works for PDFs with text layers)
            page_text = page.get_text()
            
            # Track if OCR was used
            used_ocr = False
            pix = None
            page_width = None
            page_height = None
            
            # If no text found, try OCR (only if OCR engine is available)
            if not page_text.strip():
                logger.info(f"Page {page_num + 1} has no text layer, attempting OCR with engine: {document.ocr_engine}...")
                # Render page to an image
                pix = page.get_pixmap()
                page_width = pix.width
                page_height = pix.height
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                used_ocr = True
                
                try:
                    ocr_engine_lower = document.ocr_engine.lower() if document.ocr_engine else 'mineru'
                    if ocr_engine_lower == 'pymupdf':
                        # PyMuPDF doesn't do OCR - just leave text empty if no text layer found
                        logger.info("PyMuPDF selected - no OCR fallback, leaving text empty for page without text layer")
                        page_text = ""
                        used_ocr = False
                    elif ocr_engine_lower == 'tesseract':
                        if pytesseract:
                            page_text = pytesseract.image_to_string(img)
                        else:
                            logger.warning("Tesseract selected but pytesseract not installed - skipping OCR")
                            page_text = ""  # Will create page with empty text
                            used_ocr = False
                    elif ocr_engine_lower == 'deepseek':
                        page_text = extract_text_with_deepseek_from_image(img)
                    elif ocr_engine_lower == 'pdfplumber':
                        # pdfplumber should have been handled earlier, but fallback here
                        from .ocr_utils import extract_text_with_pdfplumber
                        full_text = extract_text_with_pdfplumber(file_path, file_type='pdf')
                        page_text = full_text  # Will contain all pages text
                    elif ocr_engine_lower == 'mineru':
                        page_text = extract_text_with_mineru(file_path, file_type='pdf')
                    elif ocr_engine_lower == 'paddleocr':
                        import numpy as np
                        img_array = np.array(img)
                        from .ocr_utils import paddleocr_reader, paddleocr_available
                        if paddleocr_available and paddleocr_reader:
                            result = paddleocr_reader.ocr(img_array, cls=True)
                            if result and result[0]:
                                page_text = "\n".join([line[1][0] for line in result[0] if line and len(line) >= 2])
                            else:
                                page_text = ""
                        else:
                            logger.warning("PaddleOCR selected but not available - skipping OCR")
                            page_text = ""
                            used_ocr = False
                    elif ocr_engine_lower == 'trocr':
                        from .ocr_utils import trocr_processor, trocr_model, trocr_available
                        if trocr_available and trocr_processor and trocr_model:
                            pixel_values = trocr_processor(images=img, return_tensors="pt").pixel_values
                            generated_ids = trocr_model.generate(pixel_values)
                            page_text = trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                        else:
                            logger.warning("TrOCR selected but not available - skipping OCR")
                            page_text = ""
                            used_ocr = False
                    elif ocr_engine_lower == 'donut':
                        from .ocr_utils import donut_processor, donut_model, donut_available
                        if donut_available and donut_processor and donut_model:
                            pixel_values = donut_processor(images=img, return_tensors="pt").pixel_values
                            decoder_input_ids = donut_processor.tokenizer(
                                "<s_cord-v2>", add_special_tokens=False, return_tensors="pt"
                            ).input_ids
                            outputs = donut_model.generate(
                                pixel_values,
                                decoder_input_ids=decoder_input_ids,
                                max_length=donut_model.decoder.config.max_position_embeddings,
                                early_stopping=True,
                                pad_token_id=donut_processor.tokenizer.pad_token_id,
                                eos_token_id=donut_processor.tokenizer.eos_token_id,
                                use_cache=True,
                                num_beams=1,
                                bad_words_ids=[[donut_processor.tokenizer.unk_token_id]],
                                return_dict_in_generate=True,
                            )
                            sequence = donut_processor.batch_decode(outputs.sequences)[0]
                            sequence = sequence.replace(donut_processor.tokenizer.eos_token, "").replace(
                                donut_processor.tokenizer.pad_token, ""
                            )
                            sequence = donut_processor.token2json(sequence)
                            if isinstance(sequence, dict):
                                for key in ['text', 'text_sequence', 'texts', 'content']:
                                    if key in sequence:
                                        page_text = "\n".join(str(item) for item in sequence[key]) if isinstance(sequence[key], list) else str(sequence[key])
                                        break
                                else:
                                    page_text = str(sequence)
                            else:
                                page_text = str(sequence)
                        else:
                            logger.warning("Donut selected but not available - skipping OCR")
                            page_text = ""
                            used_ocr = False
                    elif ocr_engine_lower == 'olmocr':
                        from .ocr_utils import extract_text_with_olmocr_from_image
                        page_text = extract_text_with_olmocr_from_image(img)
                        if page_text and page_text.startswith("Error"):
                            logger.warning(f"OLMOCR failed: {page_text}")
                            page_text = ""
                            used_ocr = False
                    else:
                        # Unknown OCR engine - log warning and use empty text
                        logger.warning(f"Unknown OCR engine '{document.ocr_engine}' (normalized: '{ocr_engine_lower}') for PDF page {page_num + 1} - creating page with empty text")
                        page_text = ""
                        used_ocr = False
                except Exception as ocr_error:
                    logger.warning(f"OCR failed for page {page_num + 1}: {str(ocr_error)}")
                    page_text = ""  # Create page anyway, even without text
                    used_ocr = False
            else:
                # Text was found directly from PDF, get page dimensions
                try:
                    rect = page.rect
                    page_width = rect.width
                    page_height = rect.height
                except:
                    pass
            
            # Create basic JSON data structure for any OCR engine
            json_data = {
                'ocr_engine': ocr_engine_lower,
                'page_number': page_num + 1,
                'text': page_text.strip() if page_text else '',
                'has_ocr': used_ocr,
                'extraction_method': 'ocr' if used_ocr else 'direct',
                'page_width': page_width,
                'page_height': page_height,
            }
            
            # Use get_or_create to avoid duplicate pages
            page_obj, created = Page.objects.get_or_create(
                document=document,
                page_number=page_num + 1,
                defaults={
                    'text': page_text.strip() if page_text else '',
                    'json_data': json_data
                }
            )
            
            # Update text and JSON if page already existed
            if not created:
                page_obj.text = page_text.strip() if page_text else ''
                page_obj.json_data = json_data
                page_obj.save()
            
            pages_created += 1
            logger.info(f"{'Created' if created else 'Updated'} page {page_num + 1} (text length: {len(page_text)}, has JSON: True)")
        
        doc.close()
        logger.info(f"Successfully processed {total_pages} pages, created {pages_created} Page objects")
        
        if pages_created == 0:
            raise ValueError("Failed to create any page objects")
    
    elif document.file_type == 'image':
        # Process image file
        from .ocr_utils import extract_text_with_mineru
        
        logger.info(f"Processing image with OCR engine: {ocr_engine_lower}")
        
        if ocr_engine_lower == 'pymupdf':
            # PyMuPDF is for PDFs only, not images - use Tesseract as fallback
            logger.warning("PyMuPDF is for PDFs only, falling back to Tesseract for image processing")
            page_text = extract_text_with_tesseract(file_path) if pytesseract else ""
        elif ocr_engine_lower == 'mineru':
            page_text = extract_text_with_mineru(file_path, file_type='image')
        elif ocr_engine_lower == 'tesseract':
            page_text = extract_text_with_tesseract(file_path)
        elif ocr_engine_lower == 'deepseek':
            page_text = extract_text_with_deepseek(file_path)
        elif ocr_engine_lower == 'paddleocr':
            page_text = extract_text_with_paddleocr(file_path, file_type='image')
        elif ocr_engine_lower == 'trocr':
            page_text = extract_text_with_trocr(file_path, file_type='image')
        elif ocr_engine_lower == 'donut':
            page_text = extract_text_with_donut(file_path, file_type='image')
        elif ocr_engine_lower == 'olmocr':
            from .ocr_utils import extract_text_with_olmocr
            page_text = extract_text_with_olmocr(file_path, file_type='image')
            if page_text and page_text.startswith("Error"):
                logger.warning(f"OLMOCR failed: {page_text}")
                page_text = ""
        else:
            logger.error(f"Unknown OCR engine: {document.ocr_engine} (normalized: '{ocr_engine_lower}') - this should not happen after validation")
            page_text = f"Error: Unknown OCR engine '{document.ocr_engine}'. Please select a valid OCR engine."
        
        # Create basic JSON data structure for image processing
        json_data = {
            'ocr_engine': ocr_engine_lower,
            'page_number': 1,
            'text': page_text.strip() if page_text else '',
            'has_ocr': True,  # Images always use OCR
            'extraction_method': 'ocr',
            'file_type': 'image',
        }
        
        # Create single Page object with JSON data
        Page.objects.create(
            document=document,
            page_number=1,
            text=page_text.strip() if page_text else '',
            json_data=json_data
        )


