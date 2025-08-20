import os
import json
import sys
from dotenv import load_dotenv
from pyairtable import Api

# --- CONFIGURATION ---
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

# Airtable Client & Table Connections
api = Api(AIRTABLE_API_KEY)
applicants_table = api.table(AIRTABLE_BASE_ID, "Applicants")
personal_table = api.table(AIRTABLE_BASE_ID, "Personal Details")
experience_table = api.table(AIRTABLE_BASE_ID, "Work Experience")
salary_table = api.table(AIRTABLE_BASE_ID, "Salary Preferences")

def decompress_and_upsert(applicant_record_id):
    print(f"Starting decompression for applicant record ID: {applicant_record_id}")
    
    applicant = applicants_table.get(applicant_record_id)
    if not applicant or 'Compressed JSON' not in applicant['fields']:
        print("Error: Applicant not found or no JSON data available.")
        return

    json_str = applicant['fields']['Compressed JSON']
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in the 'Compressed JSON' field.")
        return

    applicant_display_id = applicant['fields'].get('Applicant ID', applicant_record_id)
    applicant_link_field_id = [applicant['id']]

    # Upsert Personal Details
    if 'personal' in data and data['personal']:
        personal_data = data['personal']
        personal_data['Applicant Link'] = applicant_link_field_id
        existing_personal = personal_table.first(formula=f"{{Applicant Link}}='{applicant_display_id}'")
        if existing_personal:
            personal_table.update(existing_personal['id'], personal_data)
            print("Updated Personal Details.")
        else:
            personal_table.create(personal_data)
            print("Created Personal Details.")

    # Upsert Salary Preferences
    if 'salary' in data and data['salary']:
        salary_data = data['salary']
        salary_data['Applicant Link'] = applicant_link_field_id
        existing_salary = salary_table.first(formula=f"{{Applicant Link}}='{applicant_display_id}'")
        if existing_salary:
            salary_table.update(existing_salary['id'], salary_data)
            print("Updated Salary Preferences.")
        else:
            salary_table.create(salary_data)
            print("Created Salary Preferences.")

    # Re-create Work Experience records
    if 'experience' in data:
        existing_exp_records = experience_table.all(formula=f"{{Applicant Link}}='{applicant_display_id}'")
        if existing_exp_records:
            record_ids_to_delete = [rec['id'] for rec in existing_exp_records]
            experience_table.batch_delete(record_ids_to_delete)
            print(f"Deleted {len(record_ids_to_delete)} old work experience records.")
        
        new_exp_records = []
        for exp in data['experience']:
            exp['Applicant Link'] = applicant_link_field_id
            new_exp_records.append({"fields": exp})
        
        if new_exp_records:
            experience_table.batch_create(new_exp_records)
            print(f"Created {len(new_exp_records)} new work experience records.")

    print(f"Decompression complete for {applicant_record_id}.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decompress_json.py <APPLICANT_RECORD_ID>")
        sys.exit(1)
    
    record_id = sys.argv[1]
    decompress_and_upsert(record_id)