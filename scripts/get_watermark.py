
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MDSAPP.core.managers.state_manager import StateManager

# Basic logging setup
logging.basicConfig(level=logging.INFO)

async def get_and_print_watermarks():
    """
    Initializes the StateManager and prints the current watermarks.
    """
    print("--- Fetching Watermarks from Firestore ---")
    try:
        # Load environment variables from .env file for local execution
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(dotenv_path=dotenv_path)
        
        state_manager = StateManager()
        watermarks = await state_manager.get_watermarks()

        if watermarks:
            print("Current watermarks are:")
            for service, timestamp in watermarks.items():
                print(f"  - {service}: {timestamp}")
        else:
            print("No watermarks found or the watermark document does not exist.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your environment is correctly configured with Google Cloud credentials (e.g., by running 'gcloud auth application-default login').")

if __name__ == "__main__":
    asyncio.run(get_and_print_watermarks())
