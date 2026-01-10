# xtractme
Document Extraction with Django

A Django-based document extraction and OCR application with support for multiple OCR engines including MinerU, Tesseract, DeepSeek OCR, PaddleOCR, and more.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Tesseract OCR (optional, for Tesseract OCR support)
- Git (for cloning the repository)

## Quick Start

### 1. Activate Virtual Environment

The project includes a virtual environment. Activate it:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies

If dependencies are not already installed, install them:

```bash
pip install -r requirements.txt
```

**Note:** Some dependencies (like PyTorch, PaddleOCR) are large and optional. Install only what you need.

### 3. Set Up Environment Variables (Optional)

Create a `.env` file in the project root for custom configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DEEPSEEK_OCR_API_URL=http://localhost:8001
DEEPSEEK_OCR_USE_API=True
OLLAMA_MODEL=qwen3:4b
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
```

If you don't create a `.env` file, the project will use default values from `settings.py`.

### 4. Run Database Migrations

Apply database migrations:

```bash
python manage.py migrate
```

### 5. Create Admin User (Optional)

If you need to create an admin user:

```bash
python manage.py createsuperuser
```

Or use the simple script:
```bash
python create_admin_simple.py admin admin123 admin@example.com
```

### 6. Collect Static Files

Collect static files for the admin interface:

```bash
python manage.py collectstatic --noinput
```

### 7. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The server will start at `http://localhost:8000/`

### 8. Access the Application

- **Admin Panel:** http://localhost:8000/admin/
- **Main Application:** http://localhost:8000/

## Project Structure

- `core/` - Main Django app with document extraction logic
- `myproject/` - Django project settings
- `media/` - Uploaded documents storage
- `static/` - Static files
- `staticfiles/` - Collected static files
- `docs/` - Project documentation
- `schemas/` - JSON schemas for validation

## Features

- Multiple OCR engines support (MinerU, Tesseract, DeepSeek OCR, PaddleOCR)
- Document upload and extraction
- JSON schema validation
- Modern Django admin interface (UnfoldAdmin)
- LLM integration (Ollama)
- PDF processing with PyMuPDF

## Additional Setup (Optional)

### Tesseract OCR Setup

For Tesseract OCR support, install Tesseract:

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

### DeepSeek OCR Setup

See `docs/DEEPSEEK_OCR_SETUP.md` for detailed instructions.

### MinerU Setup

See `docs/MINERU_SETUP.md` for detailed instructions.

### Ollama Setup (for LLM features)

1. Install Ollama from: https://ollama.ai
2. Pull the model:
   ```bash
   ollama pull qwen3:4b
   ```
3. Start Ollama server (usually runs automatically)

## Troubleshooting

- **Import errors:** Make sure virtual environment is activated and dependencies are installed
- **Database errors:** Run `python manage.py migrate`
- **Static files not loading:** Run `python manage.py collectstatic`
- **OCR not working:** Check that required OCR engines are properly installed

## Documentation

See the `docs/` folder for detailed documentation:
- `ADMIN_SETUP.md` - Admin user setup
- `MINERU_SETUP.md` - MinerU installation guide
- `DEEPSEEK_OCR_SETUP.md` - DeepSeek OCR setup
- `PROJECT_STRUCTURE.md` - Project structure details

## License

[Add your license information here]
