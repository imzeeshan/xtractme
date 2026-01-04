# Prompts CRUD Interface

## Overview

The Prompts CRUD (Create, Read, Update, Delete) interface allows you to manage LLM prompts directly from the Django admin panel. This provides a user-friendly way to create, edit, and manage prompt templates without modifying code.

## Accessing the Prompts Admin

1. Navigate to the Django admin panel: `http://localhost:8000/admin/`
2. Log in with your superuser credentials
3. Find **"Prompts"** in the **"Core"** section
4. Click on **"Prompts"** to view the list of prompts

## Features

### List View

The prompts list displays:
- **Title**: Display name of the prompt
- **Name**: Unique identifier (e.g., `document_summary`)
- **Category**: Category of the prompt (Document, Page, Structured Data, Custom)
- **Active**: Whether the prompt is active and available for use
- **Default**: Whether this is the default prompt for its category
- **Usage Count**: Number of times the prompt has been used
- **Created At**: When the prompt was created
- **Preview**: Button to preview the formatted prompt

### Filtering and Search

- **Filters**: Filter by category, active status, default status, and creation date
- **Search**: Search by name, title, description, or template content

### Creating a New Prompt

1. Click **"Add Prompt"** button
2. Fill in the form:
   - **Name**: Unique identifier (e.g., `my_custom_prompt`) - must be unique
   - **Title**: Display name (e.g., "My Custom Prompt")
   - **Description**: What this prompt does
   - **Category**: Select from Document, Page, Structured Data, or Custom
   - **Template**: The prompt template using `{variable_name}` for variables
   - **Active**: Check to make the prompt available for use
   - **Default**: Check to set as default for the category (only one default per category)
3. Click **"Save"**

### Editing a Prompt

1. Click on a prompt from the list
2. Modify the fields as needed
3. The **Variables** field is automatically extracted from the template
4. Click **"Save"** to update

### Deleting a Prompt

1. Select one or more prompts from the list
2. Choose **"Delete selected prompts"** from the actions dropdown
3. Click **"Go"** and confirm

### Bulk Actions

- **Activate selected prompts**: Activate multiple prompts at once
- **Deactivate selected prompts**: Deactivate multiple prompts at once
- **Reset usage count**: Reset usage statistics for selected prompts

## Template Variables

When creating or editing a prompt template, use `{variable_name}` syntax for variables that will be replaced when formatting:

### Common Variables

- `{document_title}` - Title of the document
- `{document_content}` - Full content of the document
- `{page_number}` - Page number (for page-specific prompts)
- `{total_pages}` - Total number of pages
- `{question}` - Question for Q&A prompts
- `{json_data}` - JSON data (formatted as string)
- `{custom_prompt}` - Custom prompt text

### Example Template

```
Please analyze the following document:

Document Title: {document_title}

{document_content}

Please provide:
1. A summary
2. Key points
3. Recommendations

Response:
```

## Preview Feature

The **Preview** button allows you to see how the prompt will look when formatted with sample data:

1. Click the **Preview** button next to any prompt
2. View the formatted prompt with sample variables filled in
3. This helps verify your template syntax is correct

## Syncing Built-in Prompts

To sync the built-in prompts from code to the database:

```bash
python manage.py sync_prompts
```

Options:
- `--overwrite`: Overwrite existing prompts in database
- `--category`: Only sync prompts from a specific category (document, page, structured, custom)

Example:
```bash
# Sync all prompts
python manage.py sync_prompts

# Sync and overwrite existing
python manage.py sync_prompts --overwrite

# Sync only document prompts
python manage.py sync_prompts --category document
```

## Integration with Code

The PromptManager automatically checks the database first, then falls back to built-in prompts:

```python
from core.prompts import PromptManager

# This will use database prompt if available, otherwise built-in
prompt = PromptManager.format_document_prompt(
    prompt_name='document_summary',
    document_title='My Document',
    pages_data=pages_data
)
```

## Best Practices

1. **Use descriptive names**: Choose clear, descriptive names for your prompts
2. **Document variables**: List the variables used in the description
3. **Test before using**: Use the Preview feature to test your templates
4. **Set defaults wisely**: Only set one default per category
5. **Keep templates focused**: Each prompt should have a clear, specific purpose
6. **Version control**: Consider documenting changes in the description field

## Categories

- **Document**: Prompts for full document analysis
- **Page**: Prompts for individual page analysis
- **Structured Data**: Prompts for JSON/structured data analysis
- **Custom**: Custom or specialized prompts

## Statistics

Each prompt tracks:
- **Usage Count**: How many times it has been used
- **Created By**: User who created the prompt
- **Created At**: When it was created
- **Updated At**: Last modification time

## Notes

- Database prompts take precedence over built-in prompts with the same name
- Only active prompts are available for use
- Only one prompt per category can be set as default
- Variables are automatically extracted from templates on save
- The template preview shows the first 500 characters

