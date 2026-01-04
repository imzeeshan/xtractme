"""
Management command to sync built-in prompts to the database
"""
from django.core.management.base import BaseCommand
from core.models import Prompt
from core.prompts import PromptManager
import re


class Command(BaseCommand):
    help = 'Sync built-in prompts from code to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing prompts in database',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Only sync prompts from a specific category',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        category_filter = options.get('category')
        
        # Map built-in prompt categories
        category_map = {
            'document_summary': 'document',
            'document_analysis': 'document',
            'document_extraction': 'document',
            'document_qa': 'document',
            'document_comparison': 'document',
            'document_simplification': 'document',
            'page_summary': 'page',
            'page_extraction': 'page',
            'json_analysis': 'structured',
            'table_extraction': 'structured',
            'custom': 'custom',
            'research': 'custom',
            'legal_analysis': 'custom',
            'technical_analysis': 'custom',
        }
        
        synced = 0
        skipped = 0
        errors = 0
        
        for name, prompt_template in PromptManager.PROMPTS.items():
            # Filter by category if specified
            prompt_category = category_map.get(name, 'custom')
            if category_filter and prompt_category != category_filter:
                continue
            
            try:
                prompt, created = Prompt.objects.get_or_create(
                    name=name,
                    defaults={
                        'title': prompt_template.name.replace('_', ' ').title(),
                        'description': prompt_template.description,
                        'template': prompt_template.template,
                        'category': prompt_category,
                        'is_active': True,
                        'variables': self._extract_variables(prompt_template.template),
                    }
                )
                
                if created:
                    synced += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created prompt: {name}')
                    )
                elif overwrite:
                    prompt.title = prompt_template.name.replace('_', ' ').title()
                    prompt.description = prompt_template.description
                    prompt.template = prompt_template.template
                    prompt.category = prompt_category
                    prompt.variables = self._extract_variables(prompt_template.template)
                    prompt.save()
                    synced += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Updated prompt: {name}')
                    )
                else:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f'⊘ Skipped existing prompt: {name} (use --overwrite to update)')
                    )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error syncing {name}: {str(e)}')
                )
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'Sync complete: {synced} synced, {skipped} skipped, {errors} errors')
        )

    def _extract_variables(self, template: str) -> list:
        """Extract variable names from template string"""
        # Find all {variable_name} patterns
        pattern = r'\{(\w+)\}'
        variables = re.findall(pattern, template)
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variables))

