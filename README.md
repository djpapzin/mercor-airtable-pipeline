# Mercor Interview Task: Airtable & Python Automation Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Airtable API](https://img.shields.io/badge/Airtable-API-18BFFF?logo=airtable&logoColor=white)](https://airtable.com/developers/web/api)
[![Last Commit](https://img.shields.io/github/last-commit/djpapzin/mercor-airtable-pipeline)](https://github.com/djpapzin/mercor-airtable-pipeline/commits/main)
[![Issues](https://img.shields.io/github/issues/djpapzin/mercor-airtable-pipeline)](https://github.com/djpapzin/mercor-airtable-pipeline/issues)
[![Stars](https://img.shields.io/github/stars/djpapzin/mercor-airtable-pipeline?style=social)](https://github.com/djpapzin/mercor-airtable-pipeline/stargazers)

This project is a comprehensive solution for the Mercor Tooling & AI Workflows Assessment. It demonstrates a robust data pipeline for collecting, processing, enriching, and evaluating contractor applications using Airtable as a database and local Python scripts for automation.

## Core Features

-   **Normalized Airtable Base:** A multi-table data model (`Applicants`, `Personal Details`, `Work Experience`, `Salary Preferences`) to ensure data integrity and avoid redundancy.
-   **JSON Compression:** A Python script (`process_applications.py`) that fetches data from multiple linked tables and consolidates it into a single, clean JSON object stored in the parent `Applicants` table.
-   **JSON Decompression:** A utility script (`decompress_json.py`) that can sync manual edits from the `Compressed JSON` field back to the normalized child tables for easy data maintenance.
-   **Automated Shortlisting:** A rule-based engine that automatically evaluates candidates against multi-factor criteria (e.g., years of experience, compensation, location) and creates a record in a `Shortlisted Leads` table if they are a match.
-   **Mock LLM Integration:** The system is built to integrate with an LLM for qualitative analysis (summarization, scoring, and follow-up questions). For this assessment, the live API call is mocked to allow the system to run without a paid API key, demonstrating the complete workflow.

## Technology Stack

-   **Database:** Airtable
-   **Automation / Backend:** Python 3
-   **Key Python Libraries:**
    -   `pyairtable`: For interacting with the Airtable API.
    -   `python-dotenv`: For secure management of environment variables and API keys.
    -   `openai`: The library for the original LLM integration specification.

## System Workflow

The data pipeline follows a clear, event-driven process:

1.  **Data Entry:** An applicant's information is added to the `Personal Details`, `Work Experience`, and `Salary Preferences` tables.
2.  **Record Linking:** The new records are manually linked to a central record in the `Applicants` table.
3.  **Trigger:** The `Processing Status` for the applicant is set to **`Pending`** in Airtable.
4.  **Script Execution:** The local `process_applications.py` script is executed.
5.  **Processing:** The script fetches the "Pending" record, gathers all its linked data, builds the JSON object, evaluates it against the shortlisting rules, and calls the mock LLM.
6.  **Data Update:** The script writes the `Compressed JSON`, shortlist status, and LLM enrichment data back to the `Applicants` record and sets its status to **`Completed`**.

## Setup and Usage

To run this project locally:

1.  **Prerequisites:**
    -   Python 3.8+
    -   An Airtable account
    -   A Git client

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/djpapzin/mercor-airtable-pipeline.git
    cd mercor-airtable-pipeline
    ```

3.  **Set Up a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    -   Create a file named `.env` in the root of the project folder.
    -   Add your credentials to the file. The Airtable API Key should be a **Personal Access Token (PAT)** with `data.records:read`, `data.records:write`, and `schema.bases:read` scopes.
    ```
    AIRTABLE_API_KEY="patXXXXXXXXXXXXXX"
    AIRTABLE_BASE_ID="appXXXXXXXXXXXXXX"
    OPENAI_API_KEY="not-required-for-mock-version"
    ```
    
    Note: A template is provided in `.env.example`. Copy it to `.env` and fill in your values.

6.  **Prepare Data in Airtable:**
    -   Ensure you have at least one fully linked applicant record in your Airtable base.
    -   Set the `Processing Status` for that applicant to **`Pending`**.

7.  **Run the Main Script:**
    ```bash
    python process_applications.py
    ```

The script will process the pending applicant and update the Airtable base in real-time.

## Further Documentation

For a deeper dive into the system design, table schemas, and workflows, see the detailed documentation:

- [documentation.md](https://github.com/djpapzin/mercor-airtable-pipeline/blob/main/documentation.md)
