# Generated migration for adding LightOnOCR support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_add_olmocr"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="default_ocr_engine",
            field=models.CharField(
                choices=[
                    ("mineru", "MinerU"),
                    ("tesseract", "Tesseract OCR"),
                    ("deepseek", "DeepSeek OCR"),
                    ("paddleocr", "PaddleOCR"),
                    ("trocr", "TrOCR"),
                    ("donut", "Donut"),
                    ("olmocr", "OLMOCR"),
                    ("lightonocr", "LightOnOCR-2-1B"),
                ],
                default="mineru",
                help_text="Default OCR engine to use for document processing",
                max_length=50,
            ),
        ),
    ]

