
# check_user_script.py

import asyncio
import os
from dotenv import load_dotenv
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_checks():
    """Runs a series of checks to diagnose login and Pub/Sub issues."""
    
    # --- Test 1: Check Environment Variable Loading ---
    logging.info("--- Running Test 1: Checking Environment Variables ---")
    try:
        # Load environment variables from .env file
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if not os.path.exists(dotenv_path):
            raise FileNotFoundError("CRITICAL: .env file not found.")
            
        load_dotenv(dotenv_path=dotenv_path)
        
        gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not gcp_project:
            logging.warning("FAIL: GOOGLE_CLOUD_PROJECT is not set in .env file.")
        else:
            logging.info(f"SUCCESS: GOOGLE_CLOUD_PROJECT is set to: {gcp_project}")
            
        if not gcp_creds:
            logging.warning("FAIL: GOOGLE_APPLICATION_CREDENTIALS is not set in .env file.")
        else:
            logging.info(f"SUCCESS: GOOGLE_APPLICATION_CREDENTIALS is set to: {gcp_creds}")
            if not os.path.exists(gcp_creds):
                logging.error(f"CRITICAL FAIL: The credentials file does not exist at path: {gcp_creds}")
            else:
                logging.info("SUCCESS: Credentials file path exists.")

    except Exception as e:
        logging.error(f"CRITICAL FAIL: An error occurred during Test 1: {e}", exc_info=True)
        return

    # --- Test 2: Check User Authentication ---
    logging.info("--- Running Test 2: Checking User Authentication ---")
    db_manager = None
    try:
        from MDSAPP.core.dependencies import get_database_manager
        from MDSAPP.core.security import authenticate_user

        db_manager = get_database_manager()
        # Using credentials from the screenshot
        username = "G"
        password = "Lolabep2025!!!"
        
        logging.info(f"Attempting to authenticate user '{username}'...")
        user = await authenticate_user(db_manager, username, password)
        
        if user:
            logging.info(f"SUCCESS: User '{username}' authenticated successfully.")
        else:
            logging.error(f"CRITICAL FAIL: User '{username}' failed to authenticate. Check username/password.")
            return # Stop if we can't even authenticate
            
    except Exception as e:
        logging.error(f"CRITICAL FAIL: An error occurred during Test 2: {e}", exc_info=True)
        return

    # --- Test 3: Check Google Cloud Authentication ---
    logging.info("--- Running Test 3: Initializing Pub/Sub Manager ---")
    pubsub_manager = None
    try:
        from MDSAPP.core.managers.pubsub_manager import PubSubManager
        
        logging.info("Attempting to initialize PubSubManager...")
        pubsub_manager = PubSubManager()
        
        if pubsub_manager and pubsub_manager.publisher and pubsub_manager.subscriber:
            logging.info("SUCCESS: PubSubManager initialized and authenticated with Google Cloud successfully.")
        else:
            logging.error("CRITICAL FAIL: Failed to initialize PubSubManager. This is likely an authentication issue with Google Cloud. Check credentials file and permissions.")
            return
            
    except Exception as e:
        logging.error(f"CRITICAL FAIL: An error occurred during Test 3: {e}", exc_info=True)
        return

    # --- Test 4: Check Pub/Sub Subscription ---
    logging.info("--- Running Test 4: Attempting to Create Pub/Sub Subscription ---")
    try:
        test_topic_id = f"task-updates-{username}"
        logging.info(f"Attempting to create a subscription for topic: {test_topic_id}")
        
        subscription_path = await pubsub_manager.subscribe_to_topic(test_topic_id)
        
        if subscription_path:
            logging.info(f"SUCCESS: Successfully created or found subscription: {subscription_path}")
            # Clean up the test subscription
            await pubsub_manager.delete_subscription(subscription_path)
            logging.info("SUCCESS: Cleaned up test subscription.")
        else:
            logging.error(f"CRITICAL FAIL: Failed to create subscription. The service account likely lacks Pub/Sub Editor permissions.")
            
    except Exception as e:
        logging.error(f"CRITICAL FAIL: An error occurred during Test 4: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_checks())
