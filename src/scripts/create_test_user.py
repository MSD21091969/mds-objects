import asyncio

# Importeer de benodigde componenten
from src.core.dependencies import get_database_manager
from src.core.models.user import UserInDB, UserRole
from src.core.security import get_password_hash

async def create_user():
    """Creëert een testgebruiker in de database."""
    print("Attempting to create user Sam...")
    db_manager = get_database_manager()

    username = "Sam"
    password = "Lolabep2025!!!"

    # Controleer of de gebruiker al bestaat
    existing_user = await db_manager.get("users", username)
    if existing_user:
        print(f"User '{username}' already exists. Skipping creation.")
        return

    # Maak een nieuwe gebruiker aan
    hashed_password = get_password_hash(password)
    user = UserInDB(
        username=username,
        full_name="Sam",
        email="sam@example.com",
        hashed_password=hashed_password,
        role=UserRole.ANALYST
    )

    await db_manager.save("users", user.username, user.model_dump())
    print(f"Successfully created user '{username}' with password '{password}'.")

if __name__ == "__main__":
    # Voer de asynchrone functie uit
    asyncio.run(create_user())