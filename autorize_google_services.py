# src/scripts/autorize_google_services.py

import asyncio
import os
import sys

# Add the project root to sys.path to allow for absolute imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.dependencies import (
    get_google_drive_service,
    get_google_gmail_service,
    get_google_docs_service,
    get_google_sheets_service,
    get_google_calendar_service,
    get_google_people_service,
)

async def authorize_services():
    """
    This script sequentially initializes each Google Workspace service.
    If a valid 'token.json' does not exist or lacks the required scopes,
    it will trigger the interactive OAuth 2.0 browser flow to generate one.

    Run this script once before starting the main application to ensure
    the application has a valid token with all combined scopes.
    """
    print("--- Starting Google Workspace Services Authorization ---")
    print("This will trigger a browser-based login for each service if not already authorized.")

    # Set the environment variable to allow the interactive flow
    os.environ['MDS_ALLOW_INTERACTIVE_AUTH'] = '1'

    try:
        print("\n1. Authorizing Google Drive...")
        get_google_drive_service()
        print("   Google Drive Service authorized successfully.")

        print("\n2. Authorizing Google Gmail...")
        get_google_gmail_service()
        print("   Google Gmail Service authorized successfully.")

        print("\n3. Authorizing Google Docs...")
        get_google_docs_service()
        print("   Google Docs Service authorized successfully.")

        print("\n4. Authorizing Google Sheets...")
        get_google_sheets_service()
        print("   Google Sheets Service authorized successfully.")

        print("\n5. Authorizing Google Calendar...")
        get_google_calendar_service()
        print("   Google Calendar Service authorized successfully.")

        print("\n6. Authorizing Google People...")
        get_google_people_service()
        print("   Google People Service authorized successfully.")

        print("\n--- Authorization Complete ---")
        print("A valid 'token.json' with all required scopes should now be present in the root directory.")

    except Exception as e:
        print(f"\nAn error occurred during authorization: {e}")
        print("Please ensure your 'client_secrets.json' is correctly placed in the root directory.")

if __name__ == "__main__":
    asyncio.run(authorize_services())