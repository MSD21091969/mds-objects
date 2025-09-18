
import os
import sys
# Add the project root to the Python path to allow for absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import json
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Import all scope constants from the services
from src.components.toolsets.google_workspace.drive.service import SCOPES as DRIVE_SCOPES
from src.components.toolsets.google_workspace.gmail.service import SCOPES as GMAIL_SCOPES
from src.components.toolsets.google_workspace.docs.service import SCOPES as DOCS_SCOPES
from src.components.toolsets.google_workspace.sheets.service import SCOPES as SHEETS_SCOPES
from src.components.toolsets.google_workspace.calendar.service import SCOPES as CALENDAR_SCOPES
from src.components.toolsets.google_workspace.people.service import SCOPES as PEOPLE_SCOPES

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

TOKEN_PATH = "token.json"
CLIENT_SECRETS_PATH = "client_secrets.json"

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
    if os.path.exists(TOKEN_PATH):
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
            if not os.path.exists(CLIENT_SECRETS_PATH):
                print(f"\nFATAL ERROR: {CLIENT_SECRETS_PATH} not found in the root directory.")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_PATH, all_scopes)
            creds = flow.run_local_server(port=8080)
            
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        print(f"\nCredentials saved to {TOKEN_PATH}")
    else:
        print("\nValid credentials already exist with all required scopes.")

    print("\n--- Authorization Complete ---")
    print("A 'token.json' file should now be present with all required permissions.")

if __name__ == "__main__":
    main()
