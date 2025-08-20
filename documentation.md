# Airtable Contractor Application System Documentation

This document outlines the design and implementation of an Airtable-based system for collecting, processing, and evaluating contractor applications. The system uses a normalized multi-table data model, local Python scripts for data transformation, and a mock LLM integration for qualitative analysis.

## 1. Airtable Base Setup

The system is built on a relational data model with five tables to ensure data integrity and avoid redundancy.

#### 1.1 Field Definitions

**Table: Applicants (Parent)**
The central table holding a master record for each applicant, along with processed data.
*   **Applicant ID**: `Formula` - A unique ID for each record (`RECORD_ID()`). Serves as the primary key.
*   **Personal Details Link**: `Link` - A one-to-one link to the `Personal Details` table.
*   **Work Experience Link**: `Link` - A one-to-many link to the `Work Experience` table.
*   **Salary Preferences Link**: `Link` - A one-to-one link to the `Salary Preferences` table.
*   **Processing Status**: `Single Select` - Tracks the state of the automation (`Pending`, `In Progress`, `Completed`, `Error`).
*   **Compressed JSON**: `Long Text` - Stores the consolidated JSON object from the script.
*   **JSON Hash**: `Single Line Text` - An MD5 hash of the JSON to prevent redundant processing.
*   **Shortlist Status**: `Single Select` - `Yes` or `No`, determined by the shortlisting logic.
*   **LLM Fields**: `LLM Summary`, `LLM Score`, `LLM Follow Ups`, `LLM Issues` - Fields to store the output from the LLM evaluation.

**Table: Personal Details (Child)**
*   **Full Name**: `Single Line Text` - The primary field for this table.
*   **Applicant Link**: `Link` - The link back to the `Applicants` table.
*   Other fields: `Email`, `Location`, `LinkedIn`.

**Table: Work Experience (Child)**
*   **Company**: `Single Line Text` - The primary field for this table.
*   **Applicant Link**: `Link` - The link back to the `Applicants` table.
*   Other fields: `Title`, `Start Date`, `End Date`, `Technologies`, `Years Experience` (`Formula`).

**Table: Salary Preferences (Child)**
*   **Preferred Rate**: `Number` - The primary field for this table.
*   **Applicant Link**: `Link` - The link back to the `Applicants` table.
*   Other fields: `Minimum Rate`, `Currency`, `Availability (hrs/wk)`.

**Table: Shortlisted Leads (Helper)**
*   **Name**: `Formula` - The primary field, which automatically displays the linked Applicant ID.
*   **Applicant**: `Link` - A link to the shortlisted record in the `Applicants` table.
*   **Compressed JSON**: `Long Text` - A snapshot of the applicant's JSON at the time of shortlisting.
*   **Score Reason**: `Long Text` - A human-readable explanation of why the applicant was shortlisted.

## 2. Automation and Scripts

The core logic is handled by local Python scripts that interact with the Airtable API.

#### 2.1 JSON Compression and Processing (`process_applications.py`)

This is the main script that drives the workflow.

**How it Works:**
1.  **Fetch Pending Records**: The script queries the `Applicants` table for any records with a `Processing Status` of "Pending".
2.  **Gather Linked Data**: For each pending applicant, it uses the Record IDs from the link fields to fetch the corresponding records from the `Personal Details`, `Work Experience`, and `Salary Preferences` tables.
3.  **Compress to JSON**: It consolidates the gathered data into a single, nested JSON object.
4.  **Evaluate for Shortlist**: The script checks the consolidated data against a set of predefined rules. If all criteria are met, it creates a new record in the `Shortlisted Leads` table.
5.  **LLM Evaluation**: If the applicant's data has changed (checked via an MD5 hash of the JSON), it sends the data to the LLM evaluation function.
6.  **Update Airtable**: The script performs a final update to the `Applicants` record, writing the `Compressed JSON`, shortlist status, LLM results, and setting the `Processing Status` to "Completed" or "Error".

**Code Snippet (Main Loop):**
```python
# From process_applications.py
def main():
    pending_applicants = applicants_table.all(formula="{Processing Status} = 'Pending'")
    print(f"Found {len(pending_applicants)} pending applicants.")

    for applicant in pending_applicants:
        # ... sets status to "In Progress" ...
        try:
            # 1. Fetch linked records
            # 2. Compress into JSON
            # 3. Shortlist Evaluation
            # 4. LLM Evaluation
            # 5. Update Airtable with "Completed" status
        except Exception as e:
            # ... handles any errors and sets status to "Error" ...
```

#### 2.2 JSON Decompression (`decompress_json.py`)

This utility script is designed for data maintenance, allowing manual edits to the `Compressed JSON` to be synced back to the normalized child tables.

**How it Works:**
1.  It takes an `Applicant Record ID` as an input.
2.  It reads and parses the `Compressed JSON` from that applicant's record.
3.  To ensure a perfect sync, it first deletes all existing `Work Experience` records linked to that applicant.
4.  It then upserts (updates or creates) the `Personal Details` and `Salary Preferences` records and batch-creates new `Work Experience` records based on the data in the JSON object.

## 3. LLM Integration

The system is designed to use an LLM for qualitative analysis and data enrichment.

**Configuration and Security:**
*   The API key is **not hard-coded**. It is read from a `.env` file at runtime using the `python-dotenv` library. This file is included in `.gitignore` and should not be committed to version control.
*   Authentication with Airtable now uses a **Personal Access Token (PAT)** with specific, limited scopes (`data.records:read`, `data.records:write`, `schema.bases:read`) for enhanced security over legacy API keys.
*   **For this assessment, the live LLM call was replaced with a mock function (`call_llm`)** to demonstrate the workflow without requiring a paid API key. This function returns a hard-coded sample response.

**Budget Guardrails:**
*   The system avoids redundant API calls by first checking if the applicant's data has changed. It stores an MD5 hash of the `Compressed JSON` and only calls the LLM if the new hash is different from the stored one.

## 4. How to Extend or Customize

The system is designed to be easily extensible.

**Customizing Shortlist Criteria:**
The shortlisting logic is isolated in the `evaluate_shortlist` function within `process_applications.py`.
*   **To change Tier-1 companies:** Add or remove company names from the `TIER_1_COMPANIES` list.
*   **To change allowed locations:** Modify the `ALLOWED_LOCATIONS` list.
*   **To adjust compensation rules:** Modify the conditional logic that checks `Preferred Rate`, `Currency`, and `Availability (hrs/wk)`.
*   **To add a new rule:** Add a new check within the function and a corresponding key to the `criteria_met` dictionary to ensure it is included in the final evaluation.