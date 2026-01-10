# Generated migration for adding OLMOCR support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_schema'),
    ]

    operations = [
        # Update default_ocr_engine choices to include 'olmocr'
        migrations.AlterField(
            model_name='settings',
            name='default_ocr_engine',
            field=models.CharField(
                choices=[
                    ('mineru', 'MinerU'),
                    ('tesseract', 'Tesseract OCR'),
                    ('deepseek', 'DeepSeek OCR'),
                    ('paddleocr', 'PaddleOCR'),
                    ('trocr', 'TrOCR'),
                    ('donut', 'Donut'),
                    ('olmocr', 'OLMOCR'),
                ],
                default='mineru',
                help_text='Default OCR engine to use for document processing',
                max_length=50
            ),
        ),
        # Add OLMOCR settings fields
        migrations.AddField(
            model_name='settings',
            name='olmocr_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Enable OLMOCR integration'
            ),
        ),
        migrations.AddField(
            model_name='settings',
            name='olmocr_api_url',
            field=models.URLField(
                blank=True,
                default='https://api.olmocr.com',
                help_text='OLMOCR API URL (only used if "Use OLMOCR via API" is enabled)'
            ),
        ),
        migrations.AddField(
            model_name='settings',
            name='olmocr_use_api',
            field=models.BooleanField(
                default=False,
                help_text='Use OLMOCR via API (if False, uses local installation - requires pip install olmocr)'
            ),
        ),
    ]
