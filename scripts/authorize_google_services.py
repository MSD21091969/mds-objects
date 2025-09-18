# /scripts/authorize_google_services.py

import os
import sys

# Add the project root to sys.path to allow for absolute imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the service classes and their scope constants
from src.components.toolsets.google_workspace.drive.service import GoogleDriveService, SCOPES as DRIVE_SCOPES
from src.components.toolsets.google_workspace.gmail.service import GoogleGmailService, SCOPES as GMAIL_SCOPES
from src.components.toolsets.google_workspace.docs.service import GoogleDocsService, SCOPES as DOCS_SCOPES
from src.components.toolsets.google_workspace.sheets.service import GoogleSheetsService, SCOPES as SHEETS_SCOPES
from src.components.toolsets.google_workspace.calendar.service import GoogleCalendarService, SCOPES as CALENDAR_SCOPES
from src.components.toolsets.google_workspace.people.service import GooglePeopleService, SCOPES as PEOPLE_SCOPES

# Import the flow and credentials classes to handle the OAuth 2.0 process directly.
from google_auth_oauthlib.flow import InstalledAppFlow

def get_all_service_scopes() -> list[str]:
    """
    Collects and returns a unique list of scopes from all registered Google Workspace services.
    
    This function is the single source of truth for which services require authorization.
    To add a new service, simply import its SCOPES constant and add it to the list.
    """
    all_scopes = (
        DRIVE_SCOPES +
        GMAIL_SCOPES +
        DOCS_SCOPES +
        SHEETS_SCOPES +
        CALENDAR_SCOPES +
        PEOPLE_SCOPES
    )
    return list(set(all_scopes))

def authorize_services():
    """
    This script sequentially initializes each Google Workspace service.
    If a valid 'token.json' does not exist or lacks the required scopes,
    it will trigger the interactive OAuth 2.0 browser flow to generate one.

    Run this script once before starting the main application to ensure
    the application has a valid token with all combined scopes.
    """
    print("--- Starting Google Workspace Services Authorization ---")
    print("This will trigger a browser-based login to grant permissions.")

    # To ensure all scopes are combined into a new token, we remove the old one.
    # This forces the OAuth flow to run if any permissions are missing.
    token_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'token.json'))
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
            print(f"Removed existing '{token_path}' to ensure re-authorization with all scopes.")
        except OSError as e:
            print(f"Error removing existing token.json: {e}. Please remove it manually and retry.")
            return

    # Set the environment variable to allow the interactive flow
    os.environ['MDS_ALLOW_INTERACTIVE_AUTH'] = '1'

    # Use port 0 to let the OS automatically select an available port.
    # This prevents the "[Errno 98] Address already in use" error.
    auth_port = 0

    client_secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json'))

    try:
        # Combine all scopes from all services into a single list, removing duplicates.
        all_scopes = get_all_service_scopes()

        print("\nAuthorizing all Google Workspace services at once...")
        print("This will trigger a single browser-based login if needed.")

        # Directly run the OAuth 2.0 flow to get credentials with all scopes.
        # We don't need to build a service object here; we just need to generate the token.
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, all_scopes)
        creds = flow.run_local_server(port=auth_port)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

        # We don't need to instantiate each service here anymore, as the token is now created.
        # The main application will use the generated token.json when it initializes services.
        print("\nAll services authorized successfully.")

        print("\n--- Authorization Complete ---")
        print("A valid 'token.json' with all required scopes should now be present in the root directory.")

    except Exception as e:
        print(f"\nAn error occurred during authorization: {e}")
        print("Please ensure your 'client_secrets.json' is correctly placed in the root directory.")

if __name__ == "__main__":
    authorize_services()