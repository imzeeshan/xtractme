# Sample Medical Data Extraction Prompt

## Prompt Details

**Name:** `medical_data_extraction`  
**Title:** Medical Data Extraction  
**Category:** Custom  
**Description:** Extract structured medical data from PDF documents including patient information, diagnoses, medications, lab results, and treatment plans.

## Template

```
Please extract all medical data from the following document:

Document Title: {document_title}

{document_content}

Please extract and organize the following medical information:

1. **Patient Information:**
   - Patient name or ID
   - Date of birth or age
   - Gender
   - Contact information (if available)
   - Medical record number

2. **Diagnoses:**
   - Primary diagnosis
   - Secondary diagnoses
   - ICD codes (if mentioned)
   - Diagnosis dates
   - Diagnosis status (confirmed, suspected, ruled out)

3. **Medications:**
   - Current medications with dosages
   - Medication frequency and duration
   - Prescribed medications
   - Over-the-counter medications
   - Medication allergies or adverse reactions

4. **Lab Results and Tests:**
   - Test names and dates
   - Test results with values and units
   - Reference ranges (normal values)
   - Abnormal findings
   - Imaging studies (X-rays, CT scans, MRIs, etc.)
   - Pathology results

5. **Vital Signs:**
   - Blood pressure
   - Heart rate/pulse
   - Temperature
   - Respiratory rate
   - Oxygen saturation
   - Weight and height
   - BMI (if calculated)

6. **Medical History:**
   - Past medical history
   - Surgical history
   - Family history
   - Social history (smoking, alcohol, etc.)

7. **Treatment Plans:**
   - Current treatment regimen
   - Procedures performed
   - Follow-up appointments
   - Treatment goals
   - Care plans

8. **Healthcare Providers:**
   - Attending physician
   - Consulting physicians
   - Healthcare facility
   - Department or specialty

9. **Dates and Timeline:**
   - Admission date (if applicable)
   - Discharge date (if applicable)
   - Visit dates
   - Procedure dates
   - Important medical event dates

10. **Clinical Notes:**
    - Chief complaint
    - Present illness
    - Physical examination findings
    - Assessment and plan
    - Progress notes
    - Discharge summary

11. **Additional Information:**
    - Insurance information (if mentioned)
    - Emergency contacts
    - Special instructions or precautions
    - Discharge instructions

Please format your response as a structured list with clear sections. For sensitive information, maintain privacy. If any information is not available in the document, please indicate "Not available" for that section.

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
    prompt_name='medical_data_extraction',
    document_title='Patient Medical Record - John Doe',
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
   - **Name:** `medical_data_extraction`
   - **Title:** `Medical Data Extraction`
   - **Description:** `Extract structured medical data from PDF documents`
   - **Category:** `Custom`
   - **Template:** Copy and paste the template above
   - **Active:** ✓ (checked)
3. Click **Save**

### Method 2: Via Django Shell

```python
from core.models import Prompt

prompt = Prompt.objects.create(
    name='medical_data_extraction',
    title='Medical Data Extraction',
    description='Extract structured medical data from PDF documents including patient information, diagnoses, medications, lab results, and treatment plans.',
    category='custom',
    template='''[Template content from above]''',
    is_active=True,
    variables=['document_title', 'document_content']
)
```

## Alternative: Detailed Medical Records Extraction

For more comprehensive medical record extraction:

```
You are a medical data extraction specialist. Analyze the following medical document and extract all relevant clinical information in a structured format.

Document: {document_title}

{document_content}

Extract and organize the following information:

**1. PATIENT DEMOGRAPHICS**
- Full name or patient ID
- Date of birth / Age
- Gender
- Address and contact information
- Insurance information
- Emergency contact

**2. CHIEF COMPLAINT & PRESENT ILLNESS**
- Primary reason for visit/consultation
- Duration and onset of symptoms
- Symptom description
- Associated symptoms
- Aggravating/alleviating factors

**3. MEDICAL HISTORY**
- Past medical history (chronic conditions, previous illnesses)
- Past surgical history (procedures, dates, outcomes)
- Family history (relevant genetic/hereditary conditions)
- Social history:
  * Smoking status and pack-years
  * Alcohol consumption
  * Drug use
  * Occupation
  * Living situation

**4. CURRENT MEDICATIONS**
- Prescription medications:
  * Drug name
  * Dosage
  * Frequency
  * Route of administration
  * Duration of use
- Over-the-counter medications
- Supplements and vitamins
- Medication allergies and adverse reactions

**5. VITAL SIGNS**
- Blood pressure (systolic/diastolic)
- Heart rate
- Respiratory rate
- Temperature
- Oxygen saturation
- Pain scale (if mentioned)
- Weight and height
- BMI

**6. PHYSICAL EXAMINATION**
- General appearance
- Cardiovascular findings
- Respiratory findings
- Abdominal examination
- Neurological examination
- Musculoskeletal findings
- Skin findings
- Other relevant examination findings

**7. DIAGNOSTIC TESTS & LAB RESULTS**
- Laboratory tests:
  * Test name
  * Date performed
  * Results with units
  * Reference ranges
  * Abnormal values highlighted
- Imaging studies:
  * Type (X-ray, CT, MRI, ultrasound, etc.)
  * Date performed
  * Body part/area
  * Findings/impressions
- Pathology results
- Other diagnostic procedures

**8. DIAGNOSES**
- Primary diagnosis (with ICD code if available)
- Secondary diagnoses
- Differential diagnoses considered
- Diagnosis date
- Diagnosis certainty (confirmed, probable, possible)

**9. TREATMENT & MANAGEMENT**
- Treatment plan
- Medications prescribed (new or changes)
- Procedures performed:
  * Procedure name
  * Date
  * Provider
  * Outcomes
- Therapies (physical, occupational, etc.)
- Lifestyle modifications recommended
- Follow-up care plan

**10. PROGRESS NOTES** (if applicable)
- Date of each note
- Subjective (patient's report)
- Objective (clinical findings)
- Assessment (clinical judgment)
- Plan (treatment plan)

**11. DISCHARGE INFORMATION** (if applicable)
- Discharge date
- Discharge diagnosis
- Discharge medications
- Discharge instructions
- Follow-up appointments
- Activity restrictions
- Diet modifications

**12. HEALTHCARE PROVIDERS**
- Attending physician
- Consulting physicians/specialists
- Healthcare facility name
- Department or service
- Provider contact information

**13. IMPORTANT DATES**
- Admission date (if inpatient)
- Discharge date
- Procedure dates
- Test dates
- Follow-up appointment dates
- Critical event dates

**14. CLINICAL IMPRESSIONS**
- Overall assessment
- Prognosis
- Risk factors identified
- Complications
- Recommendations

**15. ADDITIONAL NOTES**
- Special instructions
- Precautions
- Patient education provided
- Insurance authorizations
- Referrals made

Format your response with clear headings and organized sections. For each data point, include:
- The specific value or finding
- The date (if applicable)
- The context or significance
- Any relevant units or measurements

Maintain patient privacy and confidentiality. If information is not available, clearly state "Not available" for that section.

Response:
```

## Use Cases

This prompt is useful for extracting data from:
- Medical records
- Discharge summaries
- Lab reports
- Imaging reports
- Prescription documents
- Progress notes
- Consultation reports
- Insurance claim forms

## Privacy Considerations

⚠️ **Important:** Medical data is highly sensitive. Ensure:
- Proper access controls
- HIPAA compliance (if applicable)
- Secure storage and transmission
- Appropriate data retention policies
- Patient consent where required

## Testing the Prompt

After adding the prompt, you can test it:

1. Upload a medical PDF document
2. Process it to extract text
3. Use the "Send to LLM" button in the admin
4. Select `medical_data_extraction` as the prompt type
5. Review the extracted medical data

## Customization

You can customize this prompt based on your specific needs:
- Focus on specific medical specialties
- Add industry-specific terminology
- Include additional data points
- Adjust the output format
- Add validation rules

