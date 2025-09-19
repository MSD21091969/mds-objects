import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from MDSAPP.core.managers.database_manager import DatabaseManager
from MDSAPP.core.models.user import UserInDB, UserRole
from MDSAPP.core.security import get_password_hash

async def main():
    """
    Creates an admin user 'test_admin' in the Firestore database.
    """
    print("Creating admin user: test_admin")
    
    password = "password"
    hashed_password = get_password_hash(password)
    
    user_admin = UserInDB(
        username="test_admin",
        full_name="Test Admin",
        email="admin@example.com",
        hashed_password=hashed_password,
        disabled=False,
        role=UserRole.ADMIN
    )
    
    db_manager = DatabaseManager()
    
    print(f"Attempting to create user: {user_admin.username}")
    # Check if user already exists
    existing_user = await db_manager.get_user_by_username(user_admin.username)
    if existing_user:
        print(f"User '{user_admin.username}' already exists. Skipping creation.")
    else:
        await db_manager.create_user(user_admin)
        print(f"User '{user_admin.username}' created successfully.")
    
    print("\nYou can now log in with username 'test_admin' and password 'password'.")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("Please configure your GCP authentication.")
    else:
        asyncio.run(main())
