import os
import json
import time
import hashlib
from dotenv import load_dotenv
from pyairtable import Api
import openai

# --- CONFIGURATION ---
print("Loading environment variables...")
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, OPENAI_API_KEY]):
    print("ERROR: Missing one or more required environment variables (AIRTABLE_API_KEY, AIRTABLE_BASE_ID, OPENAI_API_KEY).")
    exit()

openai.api_key = OPENAI_API_KEY
print("Configuration loaded successfully.")

# Airtable Client
api = Api(AIRTABLE_API_KEY)

# Airtable Table Connections
applicants_table = api.table(AIRTABLE_BASE_ID, "Applicants")
personal_table = api.table(AIRTABLE_BASE_ID, "Personal Details")
experience_table = api.table(AIRTABLE_BASE_ID, "Work Experience")
salary_table = api.table(AIRTABLE_BASE_ID, "Salary Preferences")
shortlist_table = api.table(AIRTABLE_BASE_ID, "Shortlisted Leads")

# --- FAKE LLM EVALUATION LOGIC (DOES NOT REQUIRE API KEY) ---
def call_llm(json_data_str):
    print("DEBUG: Calling FAKE LLM... (No API key needed)")
    time.sleep(1) # Pretend it's thinking
    fake_response = {
        "summary": "This is a fake summary generated locally. The candidate shows strong potential based on the provided data.",
        "score": 8,
        "issues": "None",
        "follow_ups": "• What was your most challenging project at your previous role?\n• Can you elaborate on your experience with cloud technologies?"
    }
    print("DEBUG: Received fake response.")
    return fake_response

# --- SHORTLISTING LOGIC (COPIED FROM PREVIOUS VERSION) ---
TIER_1_COMPANIES = ['google', 'meta', 'openai', 'apple', 'amazon', 'netflix', 'microsoft', 'aws']
ALLOWED_LOCATIONS = ['us', 'canada', 'uk', 'germany', 'india']
def evaluate_shortlist(data):
    reasons = []; criteria_met = {"experience": False, "compensation": False, "location": False}
    total_exp = sum(exp.get('Years Experience', 0) for exp in data.get('experience', []))
    worked_at_tier1 = any(exp.get('Company', '').lower() in TIER_1_COMPANIES for exp in data.get('experience', []))
    if total_exp >= 4 or worked_at_tier1:
        criteria_met['experience'] = True; reasons.append(f"Experience criterion met (Total: {total_exp:.1f} years, Tier-1: {worked_at_tier1}).")
    salary = data.get('salary', {})
    if (salary.get('Preferred Rate', float('inf')) <= 100 and salary.get('Currency', '').upper() == 'USD' and salary.get('Availability (hrs/wk)', 0) >= 20):
        criteria_met['compensation'] = True; reasons.append(f"Compensation criterion met (Rate: ${salary.get('Preferred Rate')}, Availability: {salary.get('Availability (hrs/wk)')} hrs/wk).")
    location = data.get('personal', {}).get('Location', '').lower()
    if any(loc in location for loc in ALLOWED_LOCATIONS):
        criteria_met['location'] = True; reasons.append(f"Location criterion met (Location: {location.title()}).")
    return all(criteria_met.values()), "\n".join(reasons)

# --- MAIN PROCESSING SCRIPT ---
def main():
    pending_applicants = applicants_table.all(formula="{Processing Status} = 'Pending'")
    print(f"Found {len(pending_applicants)} pending applicants.")

    for applicant in pending_applicants:
        applicant_id = applicant['id']
        applicant_display_id = applicant['fields'].get('Applicant ID', applicant_id)
        print(f"--- Processing applicant {applicant_display_id} ---")
        
        applicants_table.update(applicant_id, {"Processing Status": "In Progress"})

        try:
            # === START OF DEBUGGING SECTION ===
            print("\nDEBUG: Raw data from Applicants table:")
            print(json.dumps(applicant['fields'], indent=2))

            # 1. Fetch linked record IDs
            print("\nDEBUG: Step 1 - Fetching linked record IDs...")
            personal_id_list = applicant['fields'].get('Personal Details Link', [])
            salary_id_list = applicant['fields'].get('Salary Preferences Link', [])
            experience_ids = applicant['fields'].get('Work Experience Link', [])
            
            personal_id = personal_id_list[0] if personal_id_list else None
            salary_id = salary_id_list[0] if salary_id_list else None

            print(f"  - Found Personal Details ID: {personal_id}")
            print(f"  - Found Salary Preferences ID: {salary_id}")
            print(f"  - Found Work Experience IDs: {experience_ids}")

            if not all([personal_id, salary_id, experience_ids]):
                raise ValueError("One or more required links are missing. Please check the applicant record.")

            # 2. Fetch actual records using the IDs
            print("\nDEBUG: Step 2 - Fetching actual records from other tables...")
            personal_details_rec = personal_table.get(personal_id)
            salary_prefs_rec = salary_table.get(salary_id)
            work_experience_recs = [experience_table.get(rec_id) for rec_id in experience_ids]
            print("  - Successfully fetched all linked records.")
            
            # 3. Compress into JSON
            print("\nDEBUG: Step 3 - Compressing data into JSON...")
            data = {
                "personal": personal_details_rec['fields'],
                "experience": [exp['fields'] for exp in work_experience_recs],
                "salary": salary_prefs_rec['fields']
            }
            print("  - JSON data structure created successfully.")
            
            # Clean up linked fields from JSON data
            for key in ['personal', 'salary']: data[key].pop('Applicant Link', None)
            for exp in data['experience']: exp.pop('Applicant Link', None)
            
            json_output = json.dumps(data, indent=2)
            json_hash = hashlib.md5(json_output.encode()).hexdigest()
            print("  - JSON compression complete.")
            # === END OF DEBUGGING SECTION ===

            # Shortlist Evaluation
            is_shortlisted, reason = evaluate_shortlist(data)
            shortlist_status = "Yes" if is_shortlisted else "No"
            print(f"Shortlist evaluation complete. Status: {shortlist_status}")
            
            update_payload = {
                "Compressed JSON": json_output, "JSON Hash": json_hash, "Shortlist Status": shortlist_status,
            }

            if is_shortlisted:
                existing_shortlist = shortlist_table.first(formula=f"{{Applicant}}='{applicant_display_id}'")
                if not existing_shortlist:
                    shortlist_table.create({"Applicant": [applicant_id], "Compressed JSON": json_output, "Score Reason": reason})
                    print("Created new record in Shortlisted Leads.")

            # LLM Evaluation
            if json_hash != applicant['fields'].get('JSON Hash'):
                llm_result = call_llm(json_output)
                if llm_result:
                    update_payload.update({
                        "LLM Summary": llm_result['summary'], "LLM Score": llm_result['score'],
                        "LLM Issues": llm_result['issues'], "LLM Follow Ups": llm_result['follow_ups']
                    })
            else:
                print("JSON has not changed, skipping LLM call.")
            
            # Update Airtable
            applicants_table.update(applicant_id, {**update_payload, "Processing Status": "Completed"})
            print(f"Successfully processed applicant {applicant_display_id}.")

        except Exception as e:
            # THIS IS THE MOST IMPORTANT PART - IT WILL PRINT THE EXACT ERROR
            print(f"\n\n!!!!!!!!!!!!!! AN ERROR OCCURRED !!!!!!!!!!!!!!")
            print(f"ERROR processing {applicant_display_id}: {e}")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            applicants_table.update(applicant_id, {"Processing Status": "Error"})

if __name__ == "__main__":
    main()