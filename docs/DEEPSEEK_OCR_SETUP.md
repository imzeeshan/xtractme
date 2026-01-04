# DeepSeek OCR Local Setup Guide

This guide explains how to set up and run DeepSeek OCR locally for use with this Django application.

## Option 1: Using DeepSeek OCR as a Local API Service (Recommended)

### Step 1: Clone the DeepSeek OCR Repository

```bash
git clone https://github.com/deepseek-ai/DeepSeek-OCR.git
cd DeepSeek-OCR
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv deepseek-ocr-env

# Activate virtual environment
# On Windows:
deepseek-ocr-env\Scripts\activate
# On Linux/Mac:
source deepseek-ocr-env/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install PyTorch (adjust CUDA version as needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install transformers==4.46.3 tokenizers==0.20.3
pip install fastapi uvicorn PyMuPDF Pillow
pip install einops addict easydict matplotlib

# Optional: Install FlashAttention for better performance
pip install flash-attn==2.7.3 --no-build-isolation
```

### Step 4: Download Model Weights

Download the DeepSeek-OCR model from one of these sources:

- **ModelScope**: https://www.modelscope.cn/models/deepseek-ai/DeepSeek-OCR
- **Hugging Face**: https://huggingface.co/deepseek-ai/DeepSeek-OCR

Place the downloaded model files in the `DeepSeek-OCR` directory.

### Step 5: Set Up API Server

You can use the DeepSeek-OCR WebUI which provides an API interface:

```bash
# Clone the WebUI repository
git clone https://github.com/neosun100/DeepSeek-OCR-WebUI.git
cd DeepSeek-OCR-WebUI

# Start the service
# On Windows (using Docker):
docker compose up -d

# Or run directly (if you have the dependencies):
python app.py
```

The API will be available at `http://localhost:8001`

### Step 6: Configure Django Settings

The Django application is already configured to use the local API. Check `myproject/settings.py`:

```python
DEEPSEEK_OCR_API_URL = 'http://localhost:8001'  # Adjust if needed
DEEPSEEK_OCR_USE_API = True  # Set to True to use API mode
```

## Option 2: Using DeepSeek OCR Python Package Directly

If you prefer to use the DeepSeek OCR package directly (without API server):

### Step 1: Install the Package

```bash
pip install deepseek-ocr
```

### Step 2: Update Django Settings

In `myproject/settings.py`, set:

```python
DEEPSEEK_OCR_USE_API = False  # Use direct package import
```

## Testing the Setup

### Test API Connection

You can test if the DeepSeek OCR API is running:

```bash
# Test with curl
curl -X POST http://localhost:8001/api/ocr \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64_encoded_image>"}'
```

### Test from Django

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Upload a document through the web interface
3. Select "DeepSeek OCR" as the OCR engine
4. The application will automatically connect to your local DeepSeek OCR service

## Troubleshooting

### Issue: "Could not connect to DeepSeek OCR API"

**Solutions:**
1. Ensure the DeepSeek OCR service is running on the configured port
2. Check the `DEEPSEEK_OCR_API_URL` in settings.py matches your service URL
3. Verify firewall settings allow connections to localhost:8001
4. Check the API endpoint format - different setups may use different endpoints

### Issue: "ModuleNotFoundError: No module named 'deepseek_ocr'"

**Solutions:**
1. If using API mode, this error is expected - the package is not needed
2. If using direct mode, install: `pip install deepseek-ocr`
3. Ensure your virtual environment is activated

### Issue: API Returns 404 or Connection Refused

**Solutions:**
1. Verify the API server is running: `curl http://localhost:8001/health` (if available)
2. Check the API endpoint path - try different endpoints:
   - `/api/ocr`
   - `/ocr`
   - `/api/v1/ocr`
   - `/recognize`
3. Review the DeepSeek OCR WebUI documentation for the correct endpoint

## Performance Notes

- **GPU Recommended**: DeepSeek OCR works best with a GPU (12GB+ VRAM recommended)
- **First Run**: The first run may download ~7GB of model data
- **API Mode**: Using API mode allows you to run the OCR service separately, which can be more efficient for multiple requests

## Alternative: Using Docker

If you prefer Docker:

```bash
# Clone WebUI repository
git clone https://github.com/neosun100/DeepSeek-OCR-WebUI.git
cd DeepSeek-OCR-WebUI

# Start with Docker Compose
docker compose up -d

# Check logs
docker compose logs -f
```

The service will be available at `http://localhost:8001`

## Resources

- DeepSeek OCR GitHub: https://github.com/deepseek-ai/DeepSeek-OCR
- DeepSeek OCR WebUI: https://github.com/neosun100/DeepSeek-OCR-WebUI
- Official Documentation: https://deepseekocr.org/

