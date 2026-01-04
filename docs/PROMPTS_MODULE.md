# Prompts Module Documentation

## Overview

The `core/prompts.py` module provides a centralized system for managing LLM prompts used throughout the application. It offers structured prompt templates for various document analysis tasks.

## Features

- **Structured Prompt Templates**: Pre-defined prompts for common document analysis tasks
- **Easy Customization**: Simple interface for creating and using custom prompts
- **Type Safety**: Uses dataclasses and type hints for better code quality
- **Extensible**: Easy to add new prompt types

## Available Prompts

### Document Prompts

1. **document_summary** - Generate a comprehensive summary of a document
2. **document_analysis** - Perform deep analysis of document structure and content
3. **document_extraction** - Extract specific information from a document
4. **document_qa** - Answer specific questions about a document
5. **document_comparison** - Compare two documents
6. **document_simplification** - Simplify or translate complex document content

### Page Prompts

1. **page_summary** - Summarize a single page from a document
2. **page_extraction** - Extract specific information from a page

### Structured Data Prompts

1. **json_analysis** - Analyze structured JSON data from document extraction
2. **table_extraction** - Extract and analyze table data from documents

### Custom Prompts

1. **custom** - Custom prompt with user-defined template
2. **research** - Research and analyze document for research purposes
3. **legal_analysis** - Analyze legal documents
4. **technical_analysis** - Analyze technical documentation

## Usage Examples

### Basic Usage

```python
from core.prompts import PromptManager

# Get a document summary prompt
pages_data = [
    {'page_number': 1, 'text': 'Page 1 content...'},
    {'page_number': 2, 'text': 'Page 2 content...'},
]

prompt = PromptManager.format_document_prompt(
    prompt_name='document_summary',
    document_title='My Document',
    pages_data=pages_data
)
```

### Using Convenience Functions

```python
from core.prompts import get_document_summary_prompt, get_document_analysis_prompt

# Get summary prompt
summary_prompt = get_document_summary_prompt(
    document_title='My Document',
    pages_data=pages_data
)

# Get analysis prompt
analysis_prompt = get_document_analysis_prompt(
    document_title='My Document',
    pages_data=pages_data
)
```

### Q&A Prompt

```python
from core.prompts import get_document_qa_prompt

qa_prompt = get_document_qa_prompt(
    document_title='My Document',
    pages_data=pages_data,
    question='What is the main conclusion?'
)
```

### Page-Specific Prompts

```python
from core.prompts import get_page_summary_prompt

page_prompt = get_page_summary_prompt(
    document_title='My Document',
    page_number=1,
    page_content='Page 1 content here...'
)
```

### Custom Prompts

```python
from core.prompts import PromptManager

# Use custom prompt
custom_prompt = PromptManager.format_prompt(
    prompt_name='custom',
    document_title='My Document',
    document_content='Document content...',
    custom_prompt='Please extract all email addresses from this document.'
)
```

### Listing Available Prompts

```python
from core.prompts import PromptManager

# List all available prompts
available_prompts = PromptManager.list_prompts()
for name, description in available_prompts.items():
    print(f"{name}: {description}")
```

### Using with JSON Data

```python
from core.prompts import PromptManager

json_data = {
    'pages': [
        {'page_number': 1, 'blocks': [...]},
        {'page_number': 2, 'blocks': [...]}
    ]
}

prompt = PromptManager.format_prompt(
    prompt_name='json_analysis',
    document_title='My Document',
    document_content='Document content...',
    page_number=1,
    json_data=json_data
)
```

## Integration with Admin Interface

The prompts module is integrated with the Django admin interface. When you click "Send to LLM" on a document, it uses the `document_summary` prompt by default.

You can specify a different prompt type by including it in the POST request:

```javascript
$.ajax({
    url: '/admin/core/document/' + documentId + '/send-to-llm/',
    method: 'POST',
    data: {
        'prompt_type': 'document_analysis'  // or any other prompt type
    },
    // ...
});
```

## Adding New Prompts

To add a new prompt, follow these steps:

1. **Add to appropriate class** (DocumentPrompts, PagePrompts, etc.):

```python
class DocumentPrompts:
    MY_NEW_PROMPT = PromptTemplate(
        name="my_new_prompt",
        description="Description of what this prompt does",
        template="""Your prompt template here with {variables}:
        
{document_content}

Please provide:
1. First requirement
2. Second requirement

Response:"""
    )
```

2. **Register in PromptManager.PROMPTS**:

```python
class PromptManager:
    PROMPTS = {
        # ... existing prompts
        'my_new_prompt': DocumentPrompts.MY_NEW_PROMPT,
    }
```

3. **Use the new prompt**:

```python
prompt = PromptManager.format_document_prompt(
    prompt_name='my_new_prompt',
    document_title='My Document',
    pages_data=pages_data
)
```

## Prompt Template Variables

Common variables available in prompts:

- `{document_title}` - Title of the document
- `{document_content}` - Full content of the document
- `{page_number}` - Page number (for page-specific prompts)
- `{total_pages}` - Total number of pages
- `{question}` - Question for Q&A prompts
- `{json_data}` - JSON data (formatted as string)
- `{custom_prompt}` - Custom prompt text

## Best Practices

1. **Use appropriate prompt types**: Choose the prompt that best fits your use case
2. **Keep prompts focused**: Each prompt should have a clear, specific purpose
3. **Test prompts**: Test prompts with sample documents to ensure they produce desired results
4. **Document custom prompts**: If creating custom prompts, document their purpose and expected output
5. **Handle errors**: Always handle potential errors when formatting prompts

## Examples in Codebase

The prompts module is used in:

- `core/admin.py` - Document admin interface for LLM integration
- Can be extended to other views or management commands

## Future Enhancements

Potential future improvements:

- Prompt versioning
- Prompt performance metrics
- A/B testing for prompts
- Prompt templates from database
- Multi-language prompt support

