import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- Path Setup ---
# Voeg de project-root toe aan het Python-pad.
# Dit zorgt ervoor dat imports zoals 'from src...' en 'from MDSAPP...' werken.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import all scope constants from the services
from src.agents.toolsets.googleworkspace.drive.service import SCOPES as DRIVE_SCOPES
from src.agents.toolsets.googleworkspace.gmail.service import SCOPES as GMAIL_SCOPES
from src.agents.toolsets.googleworkspace.docs.service import SCOPES as DOCS_SCOPES
from src.agents.toolsets.googleworkspace.sheets.service import SCOPES as SHEETS_SCOPES
from src.agents.toolsets.googleworkspace.calendar.service import SCOPES as CALENDAR_SCOPES
from src.agents.toolsets.googleworkspace.people.service import SCOPES as PEOPLE_SCOPES

# Load environment variables
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

TOKEN_PATH = PROJECT_ROOT / "token.json"
CLIENT_SECRETS_PATH = PROJECT_ROOT / "client_secrets.json"

def main():
    """
    This script runs a consolidated OAuth 2.0 flow to authorize all required
    Google Workspace scopes at once. This prevents port conflicts by only starting
    one local server and creates a comprehensive token.json.
    """
    print("--- Starting Google Services Authorization ---")
    
    # 1. Combine all scopes into a single unique list
    all_scopes = list(set(
        DRIVE_SCOPES + GMAIL_SCOPES + DOCS_SCOPES + 
        SHEETS_SCOPES + CALENDAR_SCOPES + PEOPLE_SCOPES
    ))
    print("\nRequesting authorization for the following permissions:")
    for scope in sorted(all_scopes):
        print(f"- {scope}")

    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if TOKEN_PATH.exists():
        # If the token exists, load it and check if it already has all the scopes.
        with open(TOKEN_PATH, 'r') as token_file:
            try:
                token_data = json.load(token_file)
                # If all scopes are already present, we can try to use the existing token.
                if all(s in token_data.get('scopes', []) for s in all_scopes):
                    creds = Credentials.from_authorized_user_file(TOKEN_PATH, all_scopes)
            except json.JSONDecodeError:
                pass # If token is malformed, it will be overwritten.
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\nCredentials expired. Refreshing token...")
            creds.refresh(Request())
        else:
            print("\nNo valid credentials found, or new permissions are needed.")
            print("Starting interactive authorization flow...")
            if not CLIENT_SECRETS_PATH.exists():
                print(f"\nFATAL ERROR: {CLIENT_SECRETS_PATH} not found in the root directory.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_PATH, all_scopes)
            creds = flow.run_local_server(port=8080)
            
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token: # This will now write to the project root
            token.write(creds.to_json())
        print(f"\nCredentials saved to {TOKEN_PATH}")
    else:
        print("\nValid credentials already exist with all required scopes.")

    print("\n--- Authorization Complete ---")
    print("A 'token.json' file should now be present with all required permissions.")

if __name__ == "__main__":
    main()