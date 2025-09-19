import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from MDSAPP.core.dependencies import get_database_manager
from MDSAPP.core.models.user import UserInDB, UserRole
from MDSAPP.core.security import get_password_hash

async def main():
    """
    Creates a requester user 'test_requester' in the Firestore database.
    """
    print("Creating requester user: test_requester")
    
    password = "password"
    hashed_password = get_password_hash(password)
    
    user_requester = UserInDB(
        username="test_requester",
        full_name="Test Requester",
        email="requester@example.com",
        hashed_password=hashed_password,
        disabled=False,
        role=UserRole.REQUESTER
    )
    
    db_manager = get_database_manager()
    
    print(f"Attempting to create user: {user_requester.username}")
    # Check if user already exists
    existing_user = await db_manager.get_user_by_username(user_requester.username)
    if existing_user:
        print(f"User '{user_requester.username}' already exists. Skipping creation.")
    else:
        await db_manager.create_user(user_requester)
        print(f"User '{user_requester.username}' created successfully.")
    
    print("\nYou can now log in with username 'test_requester' and password 'password'.")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("Please configure your GCP authentication.")
    else:
        asyncio.run(main())
