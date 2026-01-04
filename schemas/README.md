# Capital Call Document Schema

This directory contains JSON schemas for financial documents, specifically for Capital Call documents.

## Files

- `capital_call_schema.json` - JSON Schema definition for Capital Call documents
- `capital_call_example.json` - Example JSON document conforming to the schema

## Capital Call Document

A Capital Call (also known as a drawdown notice or capital commitment call) is a formal request from a fund manager to investors (limited partners) to contribute capital to the fund. This document is commonly used in:

- Private equity funds
- Venture capital funds
- Real estate investment funds
- Hedge funds
- Other alternative investment vehicles

## Schema Structure

The schema defines the following main sections:

### 1. Document Metadata
- Document type, ID, date, version, and language

### 2. Fund Information
- Fund name, ID, registration details
- Fund manager information and contact details
- Fund size and capital statistics

### 3. Call Details
- Call number, dates, and amounts
- Purpose and breakdown of capital usage
- Specific investment details

### 4. Investor Information
- Investor identification and type
- Commitment amounts and ownership percentages
- Previous contribution history
- Current call amount and remaining commitment

### 5. Payment Instructions
- Bank account details
- Wire transfer instructions
- Payment methods and references

### 6. Terms and Conditions
- Late payment penalties
- Default provisions
- Payment terms and governing law

### 7. Legal Notices
- Confidentiality notices
- Regulatory compliance
- Risk disclosures
- Tax notices

### 8. Supporting Documents
- References to related documents (LPA, subscription agreements, etc.)

### 9. Signatures
- Authorized signatories and dates

### 10. Additional Information
- Notes, contact information, and custom fields

## Usage in XtractMe

### Adding the Schema to Django

You can add this schema to your Django application using the Schema model:

```python
from core.models import Schema
import json

# Load the schema file
with open('schemas/capital_call_schema.json', 'r') as f:
    schema_data = json.load(f)

# Create the schema in the database
capital_call_schema = Schema.objects.create(
    name='capital_call_schema',
    title='Capital Call Document Schema',
    description='JSON schema for validating and structuring Capital Call documents',
    category='extraction',
    schema=schema_data,
    is_active=True,
    properties=Schema.extract_properties_from_dict(schema_data)
)
```

### Validating Extracted Data

After extracting data from a Capital Call PDF, you can validate it against the schema:

```python
from core.models import Schema

schema = Schema.objects.get(name='capital_call_schema')
is_valid, error = schema.validate_data(extracted_data)

if is_valid:
    print("Data is valid!")
else:
    print(f"Validation error: {error}")
```

### Using with OCR Extraction

1. Upload a Capital Call PDF document
2. Process it with an OCR engine (MinerU recommended for structured documents)
3. Use a prompt to extract structured data matching this schema
4. Validate the extracted JSON against this schema
5. Store the validated data in the Page model's `json_data` field

## Schema Validation

The schema follows JSON Schema Draft 7 specification. You can validate JSON documents using:

- Python: `jsonschema` library
- JavaScript: `ajv` or `jsonschema` libraries
- Online: https://www.jsonschemavalidator.net/

## Example Usage

See `capital_call_example.json` for a complete example of a valid Capital Call document in JSON format.

## Customization

You can customize this schema for your specific needs:

1. Add or remove fields based on your fund's requirements
2. Modify validation rules (min/max values, required fields)
3. Add custom fields in the `additional_information.custom_fields` section
4. Extend the schema with fund-specific sections

## Related Documents

- Limited Partnership Agreement (LPA)
- Subscription Agreement
- Side Letters
- Fund Formation Documents

## Notes

- All monetary amounts should be in the fund's base currency
- Dates should follow ISO 8601 format (YYYY-MM-DD)
- Currency codes should follow ISO 4217 standard (3-letter codes)
- Percentages are represented as numbers (e.g., 5.0 for 5%)
