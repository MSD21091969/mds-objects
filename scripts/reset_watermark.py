import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MDSAPP.core.managers.state_manager import StateManager

logging.basicConfig(level=logging.INFO)

async def reset_watermark():
    print("--- Attempting to reset watermark ---")
    try:
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)

        state_manager = StateManager()
        print(f"Deleting document 'system_state/{state_manager.doc_id}'...")
        success = await state_manager.delete_watermarks()
        if success:
            print("--- Watermark reset successfully ---")
            print("The next flow run will use the default 'days back' setting.")
        else:
            print("--- Watermark reset failed. See logs for details. ---")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("This script will permanently delete the watermark document from Firestore.")
    confirm = input("Are you sure you want to continue? (y/n): ")
    if confirm.lower() == 'y':
        asyncio.run(reset_watermark())
    else:
        print("Operation cancelled.")
