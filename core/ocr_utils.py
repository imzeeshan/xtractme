import fitz  # PyMuPDF
from PIL import Image
import requests
import base64
from io import BytesIO
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import pytesseract
    import os
    import shutil
    # Auto-detect Tesseract path on Windows if not in PATH
    if os.name == 'nt':  # Windows
        try:
            # Try to check if tesseract_cmd is already set and works
            _ = pytesseract.get_tesseract_version()
            # If this succeeds, Tesseract is already configured
        except (RuntimeError, FileNotFoundError, OSError, Exception):
            # Tesseract not found, try to auto-detect
            tesseract_found = False
            
            # First, check if tesseract is in PATH
            tesseract_in_path = shutil.which('tesseract')
            if tesseract_in_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
                logger.info(f"Tesseract found in PATH: {tesseract_in_path}")
                tesseract_found = True
            else:
                # Try common Windows installation paths
                common_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Tesseract found at: {path}")
                        tesseract_found = True
                        break
                
                # Check if a custom path is set in Django settings
                if not tesseract_found:
                    tesseract_custom_path = getattr(settings, 'TESSERACT_CMD', None)
                    if tesseract_custom_path and os.path.exists(tesseract_custom_path):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_custom_path
                        logger.info(f"Tesseract path from settings: {tesseract_custom_path}")
                        tesseract_found = True
                
                if not tesseract_found:
                    logger.warning(
                        "Tesseract not found in PATH or common installation locations. "
                        "Please install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki "
                        "or set TESSERACT_CMD in your Django settings/.env file."
                    )
except ImportError:
    pytesseract = None
except Exception as e:
    logger.warning(f"Error configuring Tesseract: {str(e)}")

# Try to import pdfplumber (will fail gracefully if not available)
# Note: pdfplumber may conflict with mineru's pdfminer.six version requirement,
# but it will gracefully fail if there are import issues
pdfplumber_available = False
try:
    import pdfplumber
    pdfplumber_available = True
except (ImportError, Exception) as e:
    # pdfplumber is optional and has dependency conflicts with mineru
    # This is expected - log at INFO level rather than WARNING
    logger.info(f"pdfplumber not available (optional dependency): {str(e)}")
    pdfplumber = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

# DeepSeek OCR - will be initialized lazily when needed
# Don't initialize at import time to avoid API key errors when not using DeepSeek OCR
deepseek_ocr = None
deepseek_ocr_initialized = False

def _init_deepseek_ocr():
    """Lazily initialize DeepSeek OCR only when needed"""
    global deepseek_ocr, deepseek_ocr_initialized
    
    if deepseek_ocr_initialized:
        return deepseek_ocr
    
    deepseek_ocr_initialized = True
    
    try:
        # Only initialize if not using API mode and not using Ollama
        use_ollama = getattr(settings, 'DEEPSEEK_OCR_USE_OLLAMA', True)
        use_api = getattr(settings, 'DEEPSEEK_OCR_USE_API', True)
        
        if not use_api and not use_ollama:
            from deepseek_ocr import DeepSeekOCR
            deepseek_ocr = DeepSeekOCR()
            logger.info("DeepSeek OCR initialized (direct mode)")
        else:
            logger.debug("DeepSeek OCR skipped (using API or Ollama mode)")
    except ImportError:
        logger.debug("DeepSeek OCR package not available")
    except Exception as e:
        logger.warning(f"Failed to initialize DeepSeek OCR: {str(e)}")
        deepseek_ocr = None
    
    return deepseek_ocr

# Try to initialize MinerU (will fail gracefully if not available)
mineru_available = False
mineru_do_parse = None
try:
    # Check if MinerU is available (newer versions use different API)
    import mineru
    # Try to import the do_parse function from CLI common module
    try:
        from mineru.cli.common import do_parse
        mineru_do_parse = do_parse
        mineru_available = True
    except (ImportError, AttributeError):
        mineru_available = False
except ImportError:
    mineru_available = False

# Try to initialize PaddleOCR (will fail gracefully if not available)
paddleocr_available = False
paddleocr_reader = None
try:
    from paddleocr import PaddleOCR
    paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
    paddleocr_available = True
except ImportError:
    paddleocr_available = False
except Exception as e:
    logger.warning(f"PaddleOCR initialization failed: {str(e)}")
    paddleocr_available = False

# Try to initialize TrOCR (Transformer OCR) (will fail gracefully if not available)
trocr_available = False
trocr_processor = None
trocr_model = None
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
    trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    trocr_available = True
except ImportError:
    trocr_available = False
except Exception as e:
    logger.warning(f"TrOCR initialization failed: {str(e)}")
    trocr_available = False

# Try to initialize Donut (Document Understanding Transformer) (will fail gracefully if not available)
donut_available = False
donut_processor = None
donut_model = None
try:
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    donut_processor = DonutProcessor.from_pretrained('naver-clova-ix/donut-base')
    donut_model = VisionEncoderDecoderModel.from_pretrained('naver-clova-ix/donut-base')
    donut_available = True
except ImportError:
    donut_available = False
except Exception as e:
    logger.warning(f"Donut initialization failed: {str(e)}")
    donut_available = False


def extract_text_with_tesseract(image_path):
    """Extract text from an image using Tesseract OCR"""
    if pytesseract is None:
        return "Error: pytesseract is not installed. Install it with: pip install pytesseract"
    try:
        # Open the image with PIL
        image = Image.open(image_path)
        # Use Tesseract to extract text
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        error_msg = str(e)
        # Check if it's a Tesseract not found error
        if "tesseract is not installed" in error_msg.lower() or "tesseract not found" in error_msg.lower() or "is not installed or it's not in your path" in error_msg.lower():
            # Provide helpful installation instructions
            install_instructions = (
                "\n\nTesseract OCR is not installed or not found in PATH.\n"
                "Windows Installation:\n"
                "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Install and check 'Add to PATH' during installation\n"
                "3. Restart your terminal/IDE after installation\n"
                "4. Or set TESSERACT_CMD in your .env file:\n"
                "   TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe\n"
                "\nSee README.md for detailed instructions."
            )
            return f"Error with Tesseract OCR: {error_msg}{install_instructions}"
        return f"Error with Tesseract OCR: {error_msg}"


def extract_text_with_mineru(file_path, file_type='pdf'):
    """Extract text from a PDF or image using MinerU"""
    if not mineru_available or mineru_do_parse is None:
        return "Error: MinerU is not installed. Install it with: pip install mineru"
    
    try:
        import tempfile
        import os
        import json
        from pathlib import Path
        
        # Read PDF bytes
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_file_name = Path(file_path).stem
            pdf_file_names = [pdf_file_name]
            pdf_bytes_list = [pdf_bytes]
            lang_list = ['en']  # Default to English, can be made configurable
            
            # Process PDF with MinerU
            mineru_do_parse(
                output_dir=temp_dir,
                pdf_file_names=pdf_file_names,
                pdf_bytes_list=pdf_bytes_list,
                p_lang_list=lang_list,
                backend='pipeline',
                parse_method='auto',
                formula_enable=True,
                table_enable=True,
                f_dump_middle_json=True,
                f_dump_md=True,
            )
            
            # Read the middle JSON output
            middle_json_path = os.path.join(temp_dir, pdf_file_name, 'auto', 'middle_json.json')
            if os.path.exists(middle_json_path):
                with open(middle_json_path, 'r', encoding='utf-8') as f:
                    middle_json = json.load(f)
                    # Extract text from all pages
                    text_parts = []
                    if 'pages' in middle_json:
                        for page in middle_json['pages']:
                            if 'blocks' in page:
                                for block in page['blocks']:
                                    if 'text' in block:
                                        text_parts.append(block['text'])
                    return '\n\n'.join(text_parts)
            else:
                # Fallback: try to read markdown output
                md_path = os.path.join(temp_dir, pdf_file_name, 'auto', 'mm_markdown.md')
                if os.path.exists(md_path):
                    with open(md_path, 'r', encoding='utf-8') as f:
                        return f.read()
                return "Error: MinerU processed but no output found"
    except Exception as e:
        logger.error(f"Error with MinerU: {str(e)}", exc_info=True)
        return f"Error with MinerU: {str(e)}"


def extract_pages_with_mineru_json(file_path):
    """Extract page-by-page JSON data from PDF using MinerU
    
    Returns:
        list: List of dictionaries, each containing:
            - page_number: int
            - text: str
            - json_data: dict (structured MinerU output)
        Returns empty list if MinerU is not available
    """
    if not mineru_available or mineru_do_parse is None:
        logger.warning("MinerU is not installed. Returning empty page data.")
        return []  # Return empty list if MinerU is not installed
    
    try:
        import tempfile
        import os
        import json
        from pathlib import Path
        
        # Read PDF bytes
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_file_name = Path(file_path).stem
            pdf_file_names = [pdf_file_name]
            pdf_bytes_list = [pdf_bytes]
            lang_list = ['en']  # Default to English, can be made configurable
            
            # Process PDF with MinerU
            mineru_do_parse(
                output_dir=temp_dir,
                pdf_file_names=pdf_file_names,
                pdf_bytes_list=pdf_bytes_list,
                p_lang_list=lang_list,
                backend='pipeline',
                parse_method='auto',
                formula_enable=True,
                table_enable=True,
                f_dump_middle_json=True,
                f_dump_md=True,
            )
            
            # Read the middle JSON output
            middle_json_path = os.path.join(temp_dir, pdf_file_name, 'auto', 'middle_json.json')
            pages_data = []
            
            if os.path.exists(middle_json_path):
                with open(middle_json_path, 'r', encoding='utf-8') as f:
                    middle_json = json.load(f)
                    
                    # Extract page-by-page data
                    if 'pages' in middle_json:
                        for idx, page_data in enumerate(middle_json['pages'], start=1):
                            page_info = {
                                'page_number': idx,
                                'text': '',
                                'json_data': page_data  # Store full page JSON
                            }
                            
                            # Extract text from blocks
                            text_parts = []
                            if 'blocks' in page_data:
                                for block in page_data['blocks']:
                                    if 'text' in block:
                                        text_parts.append(block['text'])
                            page_info['text'] = '\n\n'.join(text_parts)
                            
                            pages_data.append(page_info)
                    else:
                        # Single page or unknown format
                        text_parts = []
                        if 'blocks' in middle_json:
                            for block in middle_json['blocks']:
                                if 'text' in block:
                                    text_parts.append(block['text'])
                        pages_data.append({
                            'page_number': 1,
                            'text': '\n\n'.join(text_parts),
                            'json_data': middle_json
                        })
            
            # If no pages found, try to extract from PDF directly as fallback
            if not pages_data:
                import fitz
                doc = fitz.open(file_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'json_data': {'text': page_text, 'extracted_directly': True}
                    })
                doc.close()
            
            return pages_data
    except Exception as e:
        logger.error(f"Error extracting pages with MinerU: {str(e)}", exc_info=True)
        return []  # Return empty list on error


def extract_text_with_deepseek(image_path):
    """Extract text from an image using DeepSeek OCR (Ollama, local API, or direct)"""
    try:
        use_ollama = getattr(settings, 'DEEPSEEK_OCR_USE_OLLAMA', True)
        use_api = getattr(settings, 'DEEPSEEK_OCR_USE_API', True)
        api_url = getattr(settings, 'DEEPSEEK_OCR_API_URL', 'http://localhost:8001')
        
        logger.info(f"DeepSeek OCR: use_ollama={use_ollama}, use_api={use_api}, api_url={api_url}")
        
        # Ollama has priority - if enabled, use it exclusively
        if use_ollama:
            # Use Ollama for OCR (priority)
            logger.info("Using Ollama for DeepSeek OCR")
            result = extract_text_with_deepseek_ollama(image_path)
            # If Ollama returns an error, don't fall back to API - just return the error
            if result and result.startswith("Error"):
                return result
            return result
        elif use_api:
            logger.info(f"Using API mode for DeepSeek OCR: {api_url}")
            # Use local API server
            return extract_text_with_deepseek_api(image_path, api_url)
        else:
            # Use direct package import (lazy initialization)
            deepseek_ocr_instance = _init_deepseek_ocr()
            if deepseek_ocr_instance is None:
                return "Error: DeepSeek OCR package not available. Install it with: pip install deepseek-ocr or use Ollama/API mode."
            
            if cv2 is None:
                return "Error: OpenCV (cv2) is not installed. Install it with: pip install opencv-python-headless"
            
            # Read the image
            image = cv2.imread(str(image_path))
            if image is None:
                return "Error: Could not read the image"
            
            # Convert BGR to RGB (OpenCV uses BGR by default)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Use DeepSeek OCR
            try:
                result = deepseek_ocr_instance.recognize(image_rgb)
                return result.text
            except Exception as e:
                return f"Error with DeepSeek OCR recognition: {str(e)}"
    except Exception as e:
        return f"Error with DeepSeek OCR: {str(e)}"


def extract_text_with_deepseek_ollama(image_path):
    """Extract text from an image using Ollama vision model for OCR"""
    try:
        import ollama
        
        # Get Ollama settings
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        ollama_model = getattr(settings, 'OLLAMA_MODEL', 'qwen3:4b')
        
        # Set Ollama host if configured
        if ollama_host != 'http://localhost:11434':
            import os
            os.environ['OLLAMA_HOST'] = ollama_host
        
        # Read image file and encode to base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Create prompt for OCR
        ocr_prompt = (
            "Please extract and return all the text visible in this image. "
            "Return only the text content, preserving line breaks and spacing. "
            "Do not add any commentary or explanations, just return the extracted text."
        )
        
        # Use Ollama's chat API with image
        try:
            response = ollama.chat(
                model=ollama_model,
                messages=[
                    {
                        'role': 'user',
                        'content': ocr_prompt,
                        'images': [image_base64]
                    }
                ]
            )
            
            # Extract text from response
            extracted_text = response.get('message', {}).get('content', '')
            return extracted_text.strip()
            
        except Exception as e:
            error_msg = str(e)
            if 'Connection' in error_msg or 'connect' in error_msg.lower():
                return f"Error: Could not connect to Ollama at {ollama_host}. Please ensure Ollama is running."
            return f"Error with Ollama OCR: {error_msg}"
            
    except ImportError:
        return "Error: Ollama package is not installed. Install it with: pip install ollama"
    except Exception as e:
        return f"Error with DeepSeek OCR (Ollama): {str(e)}"


def extract_text_with_deepseek_api(image_path, api_url='http://localhost:8001'):
    """Extract text from an image using DeepSeek OCR local API server"""
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Prepare API request
        # Try common API endpoints
        endpoints = [
            f'{api_url}/api/ocr',
            f'{api_url}/ocr',
            f'{api_url}/api/v1/ocr',
            f'{api_url}/recognize',
        ]
        
        for endpoint in endpoints:
            try:
                # Try JSON payload with base64 image
                response = requests.post(
                    endpoint,
                    json={'image': image_base64},
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    # Handle different response formats
                    if isinstance(result, dict):
                        return result.get('text', result.get('result', str(result)))
                    return str(result)
            except requests.exceptions.RequestException:
                continue
            
            try:
                # Try multipart form data
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    response = requests.post(
                        endpoint,
                        files=files,
                        timeout=30
                    )
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, dict):
                        return result.get('text', result.get('result', str(result)))
                    return str(result)
            except requests.exceptions.RequestException:
                continue
        
        # If all endpoints fail, try direct file upload
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f'{api_url}/upload',
                    files=files,
                    timeout=30
                )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    return result.get('text', result.get('result', str(result)))
                return str(result)
        except requests.exceptions.RequestException:
            pass
        
        return f"Error: Could not connect to DeepSeek OCR API at {api_url}. Please ensure the service is running."
    except Exception as e:
        return f"Error with DeepSeek OCR API: {str(e)}"


def extract_text_with_deepseek_from_image(img, api_url=None):
    """Extract text from PIL Image using DeepSeek OCR (Ollama, API, or direct)"""
    try:
        use_ollama = getattr(settings, 'DEEPSEEK_OCR_USE_OLLAMA', True)
        use_api = getattr(settings, 'DEEPSEEK_OCR_USE_API', True)
        if api_url is None:
            api_url = getattr(settings, 'DEEPSEEK_OCR_API_URL', 'http://localhost:8001')
        
        logger.info(f"DeepSeek OCR from image: use_ollama={use_ollama}, use_api={use_api}, api_url={api_url}")
        
        # Ollama has priority - if enabled, use it exclusively
        if use_ollama:
            logger.info("Using Ollama for DeepSeek OCR (from image)")
            # Save PIL Image to temporary file and use Ollama
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                img.save(tmp_file.name, format='PNG')
                tmp_path = tmp_file.name
            try:
                result = extract_text_with_deepseek_ollama(tmp_path)
                # If Ollama returns an error, don't fall back to API - just return the error
                if result and result.startswith("Error"):
                    return result
                return result
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        elif use_api:
            # Convert PIL Image to bytes for API
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            endpoints = [
                f'{api_url}/api/ocr',
                f'{api_url}/ocr',
                f'{api_url}/api/v1/ocr',
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json={'image': image_base64},
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, dict):
                            return result.get('text', result.get('result', str(result)))
                        return str(result)
                except requests.exceptions.RequestException:
                    continue
            
            return "Error: Could not connect to DeepSeek OCR API"
        else:
            # Use direct package (lazy initialization)
            deepseek_ocr_instance = _init_deepseek_ocr()
            if deepseek_ocr_instance is None:
                return "Error: DeepSeek OCR package not available. Install it with: pip install deepseek-ocr or use Ollama/API mode."
            
            if cv2 is None or np is None:
                return "Error: OpenCV or NumPy not installed"
            
            try:
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                result = deepseek_ocr_instance.recognize(img_cv)
                return result.text
            except Exception as e:
                return f"Error with DeepSeek OCR recognition: {str(e)}"
    except Exception as e:
        return f"Error with DeepSeek OCR: {str(e)}"


def extract_text_with_paddleocr(file_path, file_type='pdf'):
    """Extract text from a PDF or image using PaddleOCR"""
    if not paddleocr_available or paddleocr_reader is None:
        return "Error: PaddleOCR is not installed. Install it with: pip install paddlepaddle paddleocr"
    
    try:
        if file_type == 'pdf':
            # For PDFs, convert pages to images first
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert PIL Image to numpy array for PaddleOCR
                import numpy as np
                img_array = np.array(img)
                
                # Run OCR
                result = paddleocr_reader.ocr(img_array, cls=True)
                
                # Extract text from result
                page_text = ""
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            page_text += line[1][0] + "\n"
                
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}\n")
            
            doc.close()
            return "\n".join(text_parts).strip()
        else:
            # For images
            import numpy as np
            img = Image.open(file_path)
            img_array = np.array(img)
            
            result = paddleocr_reader.ocr(img_array, cls=True)
            
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_parts.append(line[1][0])
            
            return "\n".join(text_parts).strip()
    except Exception as e:
        logger.error(f"Error with PaddleOCR: {str(e)}", exc_info=True)
        return f"Error with PaddleOCR: {str(e)}"


def extract_text_with_trocr(file_path, file_type='pdf'):
    """Extract text from a PDF or image using TrOCR (Transformer OCR)"""
    if not trocr_available or trocr_processor is None or trocr_model is None:
        return "Error: TrOCR is not installed. Install it with: pip install transformers torch"
    
    try:
        from PIL import Image
        import torch
        
        if file_type == 'pdf':
            # For PDFs, convert pages to images first
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Process with TrOCR
                pixel_values = trocr_processor(images=img, return_tensors="pt").pixel_values
                generated_ids = trocr_model.generate(pixel_values)
                generated_text = trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                text_parts.append(f"--- Page {page_num + 1} ---\n{generated_text}\n")
            
            doc.close()
            return "\n".join(text_parts).strip()
        else:
            # For images
            img = Image.open(file_path).convert('RGB')
            pixel_values = trocr_processor(images=img, return_tensors="pt").pixel_values
            generated_ids = trocr_model.generate(pixel_values)
            generated_text = trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return generated_text.strip()
    except Exception as e:
        logger.error(f"Error with TrOCR: {str(e)}", exc_info=True)
        return f"Error with TrOCR: {str(e)}"


def extract_text_with_pdfplumber(file_path, file_type='pdf'):
    """Extract text from a PDF using pdfplumber library"""
    if not pdfplumber_available or pdfplumber is None:
        return "Error: pdfplumber is not installed. Install it with: pip install pdfplumber"
    
    try:
        if file_type != 'pdf':
            return "Error: pdfplumber only works with PDF files"
        
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n\n'.join(text_parts) if text_parts else ""
    except Exception as e:
        logger.error(f"Error with pdfplumber: {str(e)}", exc_info=True)
        return f"Error with pdfplumber: {str(e)}"


def extract_text_with_donut(file_path, file_type='pdf'):
    """Extract text from a PDF or image using Donut (Document Understanding Transformer)"""
    if not donut_available or donut_processor is None or donut_model is None:
        return "Error: Donut is not installed. Install it with: pip install transformers torch"
    
    try:
        from PIL import Image
        import torch
        
        if file_type == 'pdf':
            # For PDFs, convert pages to images first
            import fitz
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Process with Donut
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
                
                # Extract text from JSON structure
                text = ""
                if isinstance(sequence, dict):
                    # Try to extract text from common keys
                    for key in ['text', 'text_sequence', 'texts', 'content']:
                        if key in sequence:
                            if isinstance(sequence[key], list):
                                text = "\n".join(str(item) for item in sequence[key])
                            else:
                                text = str(sequence[key])
                            break
                    if not text:
                        text = str(sequence)
                else:
                    text = str(sequence)
                
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}\n")
            
            doc.close()
            return "\n".join(text_parts).strip()
        else:
            # For images
            img = Image.open(file_path).convert('RGB')
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
            
            # Extract text from JSON structure
            if isinstance(sequence, dict):
                for key in ['text', 'text_sequence', 'texts', 'content']:
                    if key in sequence:
                        if isinstance(sequence[key], list):
                            return "\n".join(str(item) for item in sequence[key])
                        return str(sequence[key])
                return str(sequence)
            return str(sequence)
    except Exception as e:
        logger.error(f"Error with Donut: {str(e)}", exc_info=True)
        return f"Error with Donut: {str(e)}"


def extract_text_from_pdf(pdf_path, ocr_engine='mineru'):
    """Extract text from a PDF file with optional OCR"""
    try:
        # If pdfplumber is selected, use it (best for PDFs with text layers)
        if ocr_engine.lower() == 'pdfplumber':
            return extract_text_with_pdfplumber(pdf_path, file_type='pdf')
        
        # If MinerU is selected and available, use it
        if ocr_engine.lower() == 'mineru' and mineru_available and mineru_do_parse is not None:
            result = extract_text_with_mineru(pdf_path, file_type='pdf')
            return result
        
        # Otherwise, use traditional method
        # Open the PDF
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Try to extract text directly first
            page_text = page.get_text()
            
            # If no text found, use OCR
            if not page_text.strip():
                # Render page to an image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                if ocr_engine.lower() == 'tesseract':
                    page_text = pytesseract.image_to_string(img)
                elif ocr_engine.lower() == 'deepseek':
                    page_text = extract_text_with_deepseek_from_image(img)
                else:
                    # Default to Tesseract if unknown engine
                    page_text = pytesseract.image_to_string(img)
            
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        doc.close()
        return text.strip()
    except Exception as e:
        return f"Error processing PDF: {str(e)}"
