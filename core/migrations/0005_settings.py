# Generated migration for Settings model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_prompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('singleton_id', models.IntegerField(default=1, editable=False, unique=True)),
                ('ollama_model', models.CharField(default='qwen3:4b', help_text="Ollama model name (e.g., 'qwen3:4b', 'llama3.2')", max_length=100)),
                ('ollama_host', models.URLField(default='http://localhost:11434', help_text='Ollama server URL')),
                ('default_ocr_engine', models.CharField(choices=[('mineru', 'MinerU'), ('tesseract', 'Tesseract OCR'), ('deepseek', 'DeepSeek OCR'), ('paddleocr', 'PaddleOCR'), ('trocr', 'TrOCR'), ('donut', 'Donut')], default='mineru', help_text='Default OCR engine to use for document processing', max_length=50)),
                ('deepseek_ocr_enabled', models.BooleanField(default=True, help_text='Enable DeepSeek OCR integration')),
                ('deepseek_ocr_api_url', models.URLField(default='http://localhost:8001', help_text='DeepSeek OCR API URL')),
                ('deepseek_ocr_use_api', models.BooleanField(default=True, help_text='Use DeepSeek OCR via API (if False, uses local installation)')),
                ('site_title', models.CharField(default='Document OCR Admin', help_text='Site title displayed in admin interface', max_length=255)),
                ('site_header', models.CharField(default='Document OCR Management', help_text='Site header displayed in admin interface', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Settings',
                'verbose_name_plural': 'Settings',
            },
        ),
    ]

