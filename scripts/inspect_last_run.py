import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from firebase_admin import firestore

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MDSAPP.core.dependencies import get_database_manager

# Configure logging to be less verbose for this script
logging.basicConfig(level=logging.WARNING)

async def inspect_last_run():
    print("--- Inspecting the Most Recent Casefile ---")
    try:
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(dotenv_path=dotenv_path)

        db_manager = get_database_manager()
        
        casefiles_ref = db_manager.db.collection('casefiles')
        query = casefiles_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(1)
        
        docs = await asyncio.to_thread(query.stream)
        
        latest_casefile = next(docs, None)

        if not latest_casefile:
            print("No casefiles found.")
            return

        casefile_data = latest_casefile.to_dict()
        print(f"\n--- Details for Casefile ID: {latest_casefile.id} ---")
        print(f"Name: {casefile_data.get('name', 'N/A')}\n")

        # Drive Files
        drive_files = casefile_data.get('drive_files', [])
        print(f"--- Google Drive Files ({len(drive_files)}) ---")
        if drive_files:
            for item in drive_files:
                print(f"  - ID: {item.get('id', 'N/A')}")
        else:
            print("  (None)")

        # Gmail Messages
        gmail_messages = casefile_data.get('gmail_messages', [])
        print(f"\n--- Gmail Messages ({len(gmail_messages)}) ---")
        if gmail_messages:
            for item in gmail_messages:
                print(f"  - ID: {item.get('id', 'N/A')}")
        else:
            print("  (None)")

        # Calendar Events
        calendar_events = casefile_data.get('calendar_events', [])
        print(f"\n--- Calendar Events ({len(calendar_events)}) ---")
        if calendar_events:
            for item in calendar_events:
                print(f"  - ID: {item.get('id', 'N/A')}")
        else:
            print("  (None)")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_last_run())
