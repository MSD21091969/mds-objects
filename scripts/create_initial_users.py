import asyncio
import getpass
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
    Creates the initial admin users 'G' and 'Lola' in the Firestore database.
    """
    print("Creating initial admin users: G, Lola")
    
    try:
        password = getpass.getpass("Enter the password for both admin accounts: ")
        if not password:
            print("Password cannot be empty. Aborting.")
            return
            
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match. Aborting.")
            return

    except Exception as e:
        print(f"Could not read password: {e}")
        return

    hashed_password = get_password_hash(password)
    
    user_g = UserInDB(
        username="G",
        full_name="Admin G",
        email="g@example.com",
        hashed_password=hashed_password,
        disabled=False,
        role=UserRole.ADMIN  # Explicitly set role to admin
    )
    
    user_lola = UserInDB(
        username="Lola",
        full_name="Admin Lola",
        email="lola@example.com",
        hashed_password=hashed_password,
        disabled=False,
        role=UserRole.ADMIN  # Explicitly set role to admin
    )
    
    db_manager = DatabaseManager()
    
    print(f"Attempting to create user: {user_g.username}")
    await db_manager.create_user(user_g)
    
    print(f"Attempting to create user: {user_lola.username}")
    await db_manager.create_user(user_lola)
    
    print("\nInitial users created successfully.")
    print("You can now log in with username 'G' or 'Lola' and the password you provided.")

if __name__ == "__main__":
    # This script needs to be run in an environment where GOOGLE_APPLICATION_CREDENTIALS
    # or other GCP auth is configured.
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("Please configure your GCP authentication.")
    else:
        asyncio.run(main())
