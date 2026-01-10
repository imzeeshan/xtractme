"""
LLM Prompts Module

This module contains prompt templates for various LLM interactions.
All prompts are designed to work with Ollama and other LLM providers.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Base class for prompt templates"""
    name: str
    description: str
    template: str
    
    def format(self, **kwargs) -> str:
        """Format the prompt template with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")


class DocumentPrompts:
    """Prompts for document analysis and processing"""
    
    # Document Summary Prompt
    SUMMARY = PromptTemplate(
        name="document_summary",
        description="Generate a comprehensive summary of a document",
        template="""Please analyze the following document and provide a detailed summary:

Document Title: {document_title}

{document_content}

Please provide:
1. A brief summary of the document (2-3 sentences)
2. Key topics or themes discussed
3. Important points or findings
4. Any notable conclusions or recommendations

Response:"""
    )
    
    # Document Analysis Prompt
    ANALYSIS = PromptTemplate(
        name="document_analysis",
        description="Perform deep analysis of document structure and content",
        template="""Please perform a comprehensive analysis of the following document:

Document Title: {document_title}
Total Pages: {total_pages}

{document_content}

Please provide:
1. Document Type and Category
2. Main Topics and Themes (with brief explanations)
3. Key Information Points
4. Structure Analysis (sections, headings, etc.)
5. Important Dates, Names, or Entities mentioned
6. Conclusions or Recommendations
7. Any questions or areas that need clarification

Response:"""
    )
    
    # Document Extraction Prompt
    EXTRACTION = PromptTemplate(
        name="document_extraction",
        description="Extract specific information from a document",
        template="""Please extract the following information from the document:

Document Title: {document_title}

{document_content}

Please extract and organize:
1. Key Facts and Figures
2. Important Dates and Timelines
3. Names of People, Organizations, or Places
4. Technical Terms or Definitions
5. Action Items or Tasks (if any)
6. Contact Information (if any)

Format your response as a structured list with clear sections.

Response:"""
    )
    
    # Document Q&A Prompt
    QUESTION_ANSWER = PromptTemplate(
        name="document_qa",
        description="Answer specific questions about a document",
        template="""Based on the following document, please answer the question:

Document Title: {document_title}

{document_content}

Question: {question}

Please provide:
1. A direct answer to the question
2. Relevant context from the document
3. Page numbers or sections where the information is found (if applicable)
4. Any related information that might be helpful

Response:"""
    )
    
    # Document Comparison Prompt
    COMPARISON = PromptTemplate(
        name="document_comparison",
        description="Compare two documents",
        template="""Please compare the following two documents:

Document 1: {document1_title}
{document1_content}

Document 2: {document2_title}
{document2_content}

Please provide:
1. Similarities between the documents
2. Key differences
3. Unique points in each document
4. Overall assessment of how they relate to each other

Response:"""
    )
    
    # Document Translation/Simplification Prompt
    SIMPLIFICATION = PromptTemplate(
        name="document_simplification",
        description="Simplify or translate complex document content",
        template="""Please simplify and explain the following document in clear, accessible language:

Document Title: {document_title}

{document_content}

Please provide:
1. A simplified summary in plain language
2. Explanation of technical terms or concepts
3. Key takeaways for a general audience
4. Any important warnings or cautions

Response:"""
    )


class PagePrompts:
    """Prompts for individual page analysis"""
    
    # Page Summary Prompt
    PAGE_SUMMARY = PromptTemplate(
        name="page_summary",
        description="Summarize a single page from a document",
        template="""Please summarize the following page from a document:

Page Number: {page_number}
Document Title: {document_title}

{page_content}

Please provide:
1. Main topic or theme of this page
2. Key points discussed
3. Important information or data
4. How this page relates to the overall document (if context available)

Response:"""
    )
    
    # Page Extraction Prompt
    PAGE_EXTRACTION = PromptTemplate(
        name="page_extraction",
        description="Extract specific information from a page",
        template="""Please extract specific information from this page:

Page Number: {page_number}
Document Title: {document_title}

{page_content}

Extract:
1. Headings and subheadings
2. Key phrases or quotes
3. Numbers, dates, or statistics
4. Names or entities mentioned
5. Any structured data (tables, lists, etc.)

Response:"""
    )


class StructuredDataPrompts:
    """Prompts for structured data extraction and analysis"""
    
    # JSON Data Analysis Prompt
    JSON_ANALYSIS = PromptTemplate(
        name="json_analysis",
        description="Analyze structured JSON data from document extraction",
        template="""Please analyze the following structured document data:

Document Title: {document_title}
Page Number: {page_number}

JSON Data:
{json_data}

Please provide:
1. Overview of the document structure
2. Key content elements identified
3. Relationships between different elements
4. Any missing or incomplete information
5. Suggestions for data organization or categorization

Response:"""
    )
    
    # Table Extraction Prompt
    TABLE_EXTRACTION = PromptTemplate(
        name="table_extraction",
        description="Extract and analyze table data from documents",
        template="""Please extract and analyze table data from the following document:

Document Title: {document_title}
Page Number: {page_number}

{document_content}

Please:
1. Identify any tables in the content
2. Extract table data in a structured format
3. Explain what the tables represent
4. Highlight key insights or patterns in the data

Response:"""
    )


class CustomPrompts:
    """Custom and specialized prompts"""
    
    # Custom Prompt Template
    CUSTOM = PromptTemplate(
        name="custom",
        description="Custom prompt with user-defined template",
        template="{custom_prompt}\n\nDocument Content:\n{document_content}\n\nResponse:"
    )
    
    # Research Prompt
    RESEARCH = PromptTemplate(
        name="research",
        description="Research and analyze document for research purposes",
        template="""Please analyze this document from a research perspective:

Document Title: {document_title}

{document_content}

Please provide:
1. Research questions this document addresses
2. Methodology or approach used (if applicable)
3. Key findings or results
4. Limitations or areas for further research
5. Relevance to broader research field

Response:"""
    )
    
    # Legal Document Analysis
    LEGAL_ANALYSIS = PromptTemplate(
        name="legal_analysis",
        description="Analyze legal documents",
        template="""Please analyze this legal document:

Document Title: {document_title}

{document_content}

Please provide:
1. Document type and purpose
2. Key parties involved
3. Important terms and conditions
4. Obligations and responsibilities
5. Dates and deadlines
6. Any potential concerns or areas requiring attention

Note: This is for informational purposes only and does not constitute legal advice.

Response:"""
    )
    
    # Technical Documentation Analysis
    TECHNICAL_ANALYSIS = PromptTemplate(
        name="technical_analysis",
        description="Analyze technical documentation",
        template="""Please analyze this technical document:

Document Title: {document_title}

{document_content}

Please provide:
1. Technology or system being documented
2. Key technical concepts explained
3. Procedures or processes described
4. Configuration or setup requirements
5. Troubleshooting information (if any)
6. Dependencies or prerequisites

Response:"""
    )


class PromptManager:
    """Manager class for handling prompts"""
    
    # Registry of all available built-in prompts
    PROMPTS = {
        # Document prompts
        'document_summary': DocumentPrompts.SUMMARY,
        'document_analysis': DocumentPrompts.ANALYSIS,
        'document_extraction': DocumentPrompts.EXTRACTION,
        'document_qa': DocumentPrompts.QUESTION_ANSWER,
        'document_comparison': DocumentPrompts.COMPARISON,
        'document_simplification': DocumentPrompts.SIMPLIFICATION,
        
        # Page prompts
        'page_summary': PagePrompts.PAGE_SUMMARY,
        'page_extraction': PagePrompts.PAGE_EXTRACTION,
        
        # Structured data prompts
        'json_analysis': StructuredDataPrompts.JSON_ANALYSIS,
        'table_extraction': StructuredDataPrompts.TABLE_EXTRACTION,
        
        # Custom prompts
        'custom': CustomPrompts.CUSTOM,
        'research': CustomPrompts.RESEARCH,
        'legal_analysis': CustomPrompts.LEGAL_ANALYSIS,
        'technical_analysis': CustomPrompts.TECHNICAL_ANALYSIS,
    }
    
    @classmethod
    def get_prompt(cls, prompt_name: str, use_database: bool = True) -> Optional[PromptTemplate]:
        """
        Get a prompt template by name
        
        Args:
            prompt_name: Name of the prompt
            use_database: If True, check database first, then fall back to built-in prompts
            
        Returns:
            PromptTemplate or None
        """
        # Try to get from database first if enabled
        if use_database:
            try:
                from .models import Prompt
                db_prompt = Prompt.objects.filter(
                    name=prompt_name,
                    is_active=True
                ).first()
                
                if db_prompt:
                    # Convert database prompt to PromptTemplate
                    return PromptTemplate(
                        name=db_prompt.name,
                        description=db_prompt.description or '',
                        template=db_prompt.template
                    )
            except Exception:
                # If database is not available or model doesn't exist yet, fall back
                pass
        
        # Fall back to built-in prompts
        return cls.PROMPTS.get(prompt_name)
    
    @classmethod
    def list_prompts(cls, include_database: bool = True) -> Dict[str, str]:
        """
        List all available prompts with display names
        
        Args:
            include_database: If True, include prompts from database
            
        Returns:
            Dictionary mapping prompt names to display names
        """
        prompts = {}
        
        # Add database prompts if enabled
        if include_database:
            try:
                from .models import Prompt
                db_prompts = Prompt.objects.filter(is_active=True).order_by('category', 'title')
                for db_prompt in db_prompts:
                    # Use title as display name, fallback to description, then formatted name
                    display_name = db_prompt.title or db_prompt.description or cls._format_prompt_name(db_prompt.name)
                    prompts[db_prompt.name] = display_name
            except Exception:
                # If database is not available, skip
                pass
        
        # Add built-in prompts (database prompts take precedence if same name)
        for name, prompt in cls.PROMPTS.items():
            if name not in prompts:
                # Format the name to be more user-friendly (e.g., "document_summary" -> "Document Summary")
                display_name = cls._format_prompt_name(name)
                prompts[name] = display_name
        
        return prompts
    
    @staticmethod
    def _format_prompt_name(name: str) -> str:
        """Convert prompt name to display-friendly format"""
        # Replace underscores with spaces and title case
        return name.replace('_', ' ').title()
    
    @classmethod
    def format_prompt(
        cls, 
        prompt_name: str, 
        document_title: str = "",
        document_content: str = "",
        page_number: Optional[int] = None,
        total_pages: Optional[int] = None,
        question: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        custom_prompt: Optional[str] = None,
        use_database: bool = True,
        **kwargs
    ) -> str:
        """
        Format a prompt with common variables
        
        Args:
            prompt_name: Name of the prompt template to use
            document_title: Title of the document
            document_content: Content of the document
            page_number: Page number (for page-specific prompts)
            total_pages: Total number of pages
            question: Question for Q&A prompts
            json_data: JSON data for structured analysis
            custom_prompt: Custom prompt text
            use_database: If True, check database first for prompts
            **kwargs: Additional variables for custom prompts
            
        Returns:
            Formatted prompt string
        """
        prompt_template = cls.get_prompt(prompt_name, use_database=use_database)
        if not prompt_template:
            available = list(cls.list_prompts(include_database=use_database).keys())
            raise ValueError(f"Unknown prompt: {prompt_name}. Available: {available}")
        
        # Prepare common variables
        variables = {
            'document_title': document_title,
            'document_content': document_content,
            **kwargs
        }
        
        # Add optional variables if provided
        if page_number is not None:
            variables['page_number'] = page_number
        if total_pages is not None:
            variables['total_pages'] = total_pages
        if question is not None:
            variables['question'] = question
        if json_data is not None:
            import json
            variables['json_data'] = json.dumps(json_data, indent=2, ensure_ascii=False)
        if custom_prompt is not None:
            variables['custom_prompt'] = custom_prompt
        
        return prompt_template.format(**variables)
    
    @classmethod
    def format_document_prompt(
        cls,
        prompt_name: str,
        document_title: str,
        pages_data: List[Dict[str, Any]],
        use_database: bool = True,
        **kwargs
    ) -> str:
        """
        Format a prompt for a full document with multiple pages
        
        Args:
            prompt_name: Name of the prompt template
            document_title: Title of the document
            pages_data: List of page data dicts with 'page_number', 'text', and optionally 'json_data' keys
            use_database: If True, check database first for prompts
            **kwargs: Additional variables
            
        Returns:
            Formatted prompt string
        """
        import json
        # Combine all pages into a single content string
        document_content = f"Document: {document_title}\n\n"
        json_data_all = []  # Collect all JSON data for structured analysis
        
        for page_data in pages_data:
            page_num = page_data.get('page_number', '?')
            page_text = page_data.get('text', '')
            page_json = page_data.get('json_data')
            
            document_content += f"--- Page {page_num} ---\n{page_text}\n\n"
            
            # If JSON data exists, include it in the content
            if page_json:
                try:
                    json_str = json.dumps(page_json, indent=2, ensure_ascii=False)
                    document_content += f"--- Page {page_num} Structured Data (JSON) ---\n{json_str}\n\n"
                    json_data_all.append({
                        'page_number': page_num,
                        'json_data': page_json
                    })
                except Exception:
                    # If JSON serialization fails, skip it
                    pass
        
        # If we have JSON data, include it as a separate variable for prompts that use it
        kwargs_with_json = kwargs.copy()
        if json_data_all:
            # Combine all JSON data into a single structure
            if len(json_data_all) == 1:
                kwargs_with_json['json_data'] = json_data_all[0]['json_data']
            else:
                # Multiple pages with JSON - create a combined structure
                kwargs_with_json['json_data'] = {
                    'pages': json_data_all,
                    'total_pages_with_json': len(json_data_all)
                }
        
        return cls.format_prompt(
            prompt_name=prompt_name,
            document_title=document_title,
            document_content=document_content,
            total_pages=len(pages_data),
            use_database=use_database,
            **kwargs_with_json
        )
    
    @classmethod
    def format_page_prompt(
        cls,
        prompt_name: str,
        document_title: str,
        page_number: int,
        page_content: str,
        use_database: bool = True,
        **kwargs
    ) -> str:
        """
        Format a prompt for a single page
        
        Args:
            prompt_name: Name of the prompt template
            document_title: Title of the document
            page_number: Page number
            page_content: Content of the page
            **kwargs: Additional variables
            
        Returns:
            Formatted prompt string
        """
        return cls.format_prompt(
            prompt_name=prompt_name,
            document_title=document_title,
            document_content=page_content,
            page_number=page_number,
            use_database=use_database,
            **kwargs
        )


# Convenience functions for common use cases
def get_document_summary_prompt(document_title: str, pages_data: List[Dict[str, Any]]) -> str:
    """Get a formatted document summary prompt"""
    return PromptManager.format_document_prompt(
        'document_summary',
        document_title,
        pages_data
    )


def get_document_analysis_prompt(document_title: str, pages_data: List[Dict[str, Any]]) -> str:
    """Get a formatted document analysis prompt"""
    return PromptManager.format_document_prompt(
        'document_analysis',
        document_title,
        pages_data
    )


def get_document_qa_prompt(document_title: str, pages_data: List[Dict[str, Any]], question: str) -> str:
    """Get a formatted Q&A prompt"""
    return PromptManager.format_document_prompt(
        'document_qa',
        document_title,
        pages_data,
        question=question
    )


def get_page_summary_prompt(document_title: str, page_number: int, page_content: str) -> str:
    """Get a formatted page summary prompt"""
    return PromptManager.format_page_prompt(
        'page_summary',
        document_title,
        page_number,
        page_content
    )

