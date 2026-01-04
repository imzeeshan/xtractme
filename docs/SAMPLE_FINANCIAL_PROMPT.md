# Sample Financial Data Extraction Prompt

## Prompt Details

**Name:** `financial_data_extraction`  
**Title:** Financial Data Extraction  
**Category:** Custom  
**Description:** Extract structured financial data from PDF documents including revenue, expenses, profits, dates, and key financial metrics.

## Template

```
Please extract all financial data from the following document:

Document Title: {document_title}

{document_content}

Please extract and organize the following financial information:

1. **Revenue/Income:**
   - Total revenue
   - Revenue by period (if available)
   - Revenue by category/segment (if available)

2. **Expenses:**
   - Total expenses
   - Operating expenses
   - Cost of goods sold (COGS)
   - Other expenses by category

3. **Profit/Loss:**
   - Gross profit
   - Operating profit
   - Net profit/loss
   - Profit margins (if available)

4. **Financial Metrics:**
   - EBITDA (if mentioned)
   - Cash flow information
   - Assets and liabilities
   - Equity information

5. **Dates and Periods:**
   - Reporting period (e.g., Q1 2024, FY 2023)
   - Specific dates mentioned
   - Comparison periods (if any)

6. **Key Financial Figures:**
   - Any specific numbers, percentages, or ratios
   - Growth rates or changes
   - Budget vs actual (if applicable)

7. **Additional Information:**
   - Company/organization name
   - Currency (if specified)
   - Any notes or disclaimers

Please format your response as a structured list with clear sections. If any information is not available in the document, please indicate "Not available" for that section.

Response:
```

## Variables Used

- `{document_title}` - Title of the document
- `{document_content}` - Full content extracted from the PDF

## Usage Example

```python
from core.prompts import PromptManager

# Format the prompt
prompt = PromptManager.format_document_prompt(
    prompt_name='financial_data_extraction',
    document_title='Q4 2024 Financial Report',
    pages_data=[
        {'page_number': 1, 'text': 'Page 1 content...'},
        {'page_number': 2, 'text': 'Page 2 content...'},
    ]
)
```

## Adding to Database

You can add this prompt to your database in two ways:

### Method 1: Via Django Admin

1. Go to `/admin/core/prompt/add/`
2. Fill in the form:
   - **Name:** `financial_data_extraction`
   - **Title:** `Financial Data Extraction`
   - **Description:** `Extract structured financial data from PDF documents`
   - **Category:** `Custom`
   - **Template:** Copy and paste the template above
   - **Active:** ✓ (checked)
3. Click **Save**

### Method 2: Via Django Shell

```python
from core.models import Prompt

prompt = Prompt.objects.create(
    name='financial_data_extraction',
    title='Financial Data Extraction',
    description='Extract structured financial data from PDF documents including revenue, expenses, profits, dates, and key financial metrics.',
    category='custom',
    template='''Please extract all financial data from the following document:

Document Title: {document_title}

{document_content}

Please extract and organize the following financial information:

1. **Revenue/Income:**
   - Total revenue
   - Revenue by period (if available)
   - Revenue by category/segment (if available)

2. **Expenses:**
   - Total expenses
   - Operating expenses
   - Cost of goods sold (COGS)
   - Other expenses by category

3. **Profit/Loss:**
   - Gross profit
   - Operating profit
   - Net profit/loss
   - Profit margins (if available)

4. **Financial Metrics:**
   - EBITDA (if mentioned)
   - Cash flow information
   - Assets and liabilities
   - Equity information

5. **Dates and Periods:**
   - Reporting period (e.g., Q1 2024, FY 2023)
   - Specific dates mentioned
   - Comparison periods (if any)

6. **Key Financial Figures:**
   - Any specific numbers, percentages, or ratios
   - Growth rates or changes
   - Budget vs actual (if applicable)

7. **Additional Information:**
   - Company/organization name
   - Currency (if specified)
   - Any notes or disclaimers

Please format your response as a structured list with clear sections. If any information is not available in the document, please indicate "Not available" for that section.

Response:''',
    is_active=True,
    variables=['document_title', 'document_content']
)
```

## Alternative: More Detailed Financial Prompt

If you need a more detailed extraction, here's an enhanced version:

```
You are a financial data extraction specialist. Analyze the following document and extract all financial information in a structured format.

Document: {document_title}

{document_content}

Extract the following information and organize it clearly:

**1. COMPANY INFORMATION**
- Company/Organization name
- Reporting period (e.g., "Q4 2024", "Fiscal Year 2023")
- Currency used
- Date of report

**2. REVENUE/INCOME STATEMENT**
- Total revenue/income
- Revenue breakdown by:
  * Product/service lines
  * Geographic regions
  * Business segments
- Revenue trends (growth/decline percentages)
- Recurring vs one-time revenue

**3. EXPENSES**
- Total expenses
- Operating expenses breakdown:
  * Salaries and wages
  * Rent and utilities
  * Marketing and advertising
  * Research and development
  * Other operating expenses
- Cost of goods sold (COGS)
- Interest expenses
- Tax expenses
- Other non-operating expenses

**4. PROFITABILITY**
- Gross profit (Revenue - COGS)
- Gross profit margin (%)
- Operating profit (EBIT)
- Operating profit margin (%)
- EBITDA
- Net profit/loss
- Net profit margin (%)
- Earnings per share (if applicable)

**5. BALANCE SHEET ITEMS** (if available)
- Total assets
- Current assets
- Fixed assets
- Total liabilities
- Current liabilities
- Long-term liabilities
- Shareholders' equity
- Debt-to-equity ratio (if calculable)

**6. CASH FLOW** (if available)
- Operating cash flow
- Investing cash flow
- Financing cash flow
- Net change in cash
- Cash at beginning/end of period

**7. KEY RATIOS AND METRICS**
- Current ratio
- Quick ratio
- Return on assets (ROA)
- Return on equity (ROE)
- Any other financial ratios mentioned

**8. COMPARATIVE DATA**
- Year-over-year comparisons
- Quarter-over-quarter comparisons
- Budget vs actual (if provided)
- Forecasts or projections

**9. NOTES AND DISCLOSURES**
- Accounting methods used
- Significant events or changes
- Risk factors mentioned
- Management commentary

**10. TABLES AND CHARTS**
- Extract data from any financial tables
- Summarize information from charts/graphs

Format your response with clear headings and bullet points. For each section, include:
- The specific value/number
- The unit (currency, percentage, etc.)
- The time period it relates to
- Any relevant context or notes

If information is not available in the document, clearly state "Not available" for that section.

Response:
```

## Testing the Prompt

After adding the prompt, you can test it:

1. Upload a financial PDF document
2. Process it to extract text
3. Use the "Send to LLM" button in the admin
4. Select `financial_data_extraction` as the prompt type
5. Review the extracted financial data

## Customization

You can customize this prompt based on your specific needs:
- Add industry-specific metrics
- Focus on particular financial statements
- Include additional data points
- Adjust the output format

