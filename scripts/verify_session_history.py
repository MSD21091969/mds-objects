# scripts/verify_session_history.py

import asyncio
import sys
import os
from dotenv import load_dotenv
import logging

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging to be less verbose for this script
logging.basicConfig(level=logging.WARNING)

from MDSAPP.core.services.firestore_session_service import FirestoreSessionService

async def main():
    """
    Fetches a specific session from Firestore and reports on its history.
    """
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found. Assuming environment variables are set.")

    print("--- Session History Verification Tool ---")
    
    session_id = input("Please enter the full session ID to verify (e.g., conv-Lola-case-xyz...): ")
    if not session_id:
        print("Error: Session ID cannot be empty.")
        return

    try:
        session_service = FirestoreSessionService()
        session = await session_service.get_session(session_id)

        if not session:
            print(f"\nRESULT: Session with ID '{session_id}' not found in Firestore.")
            return

        history_count = len(session.history)
        
        print("\n-------------------------------------------")
        print(f"RESULT for session: {session.id}")
        print(f"Total messages found in Firestore history: {history_count}")
        print("-------------------------------------------")
        
        print("\nExpected history count is (Number of User Messages * 2).")
        print("For example, if you sent 3 messages, the count should be 6.")
        
        print("\nFull History Log:")
        for i, message in enumerate(session.history):
            # Assuming parts[0] exists and has a 'text' key
            text_preview = message.parts[0].get('text', '[No text found]')[:80] + "..."
            print(f"  {i+1}. Role: {message.role.ljust(10)} | Text: \"{text_preview}\"")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure your GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT are correct.")

if __name__ == "__main__":
    asyncio.run(main())
