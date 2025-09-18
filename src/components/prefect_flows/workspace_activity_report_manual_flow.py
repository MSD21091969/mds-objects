# MDSAPP/prefect_flows/workspace_activity_report_manual_flow.py

import os
import asyncio
from prefect import flow, get_run_logger

from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

# Import shared tasks
from .shared_tasks import (
    fetch_drive_files_task,
    fetch_gmail_messages_task,
    fetch_calendar_events_task,
    process_attachments_task,
    create_report_casefile_task,
    aggregate_and_save_task,
)

# --- Pydantic Models for Flow ---
class ManualWorkspaceActivityFlowParameters(BaseModel):
    user_id: str = Field(default="prefect_user", description="The user ID to associate with the run.")
    start_date: str = Field(description="The start date for the report in ISO format (e.g., '2023-01-01T00:00:00Z').")
    end_date: Optional[str] = Field(default=None, description="Optional end date in ISO format. Defaults to now if not provided.")

# --- Main Flow ---

@flow(name="Google Workspace Manual Sync Flow")
async def workspace_activity_report_manual_flow(parameters: ManualWorkspaceActivityFlowParameters):
    logger = get_run_logger()
    logger.info(f"Starting Google Workspace Manual Sync flow for {parameters.user_id}.")

    # --- Date Range Calculation ---
    try:
        start_time = datetime.fromisoformat(parameters.start_date)
        if parameters.end_date:
            end_time = datetime.fromisoformat(parameters.end_date)
        else:
            end_time = datetime.now(timezone.utc)
        
        if start_time.tzinfo is None: start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None: end_time = end_time.replace(tzinfo=timezone.utc)

    except ValueError as e:
        logger.error(f"Invalid date format provided: {e}. Please use ISO format.")
        return {"status": "error", "message": "Invalid date format."}

    date_range = {"start_time": start_time, "end_time": end_time}
    logger.info(f"Processing manual date range from {date_range['start_time']} to {date_range['end_time']}.")

    # Concurrently fetch data
    drive_files_task = fetch_drive_files_task.submit(date_range)
    gmail_messages_task = fetch_gmail_messages_task.submit(date_range)
    calendar_events_task = fetch_calendar_events_task.submit(date_range)

    drive_files = drive_files_task.result()
    gmail_messages = gmail_messages_task.result()
    calendar_events = calendar_events_task.result()

    if not drive_files and not gmail_messages and not calendar_events:
        logger.info("No new activity found for the specified date range. Flow finished.")
        return {"status": "success", "message": "No new activity."}

    casefile_id_task = create_report_casefile_task.submit(
        user_id=parameters.user_id, 
        start_time=date_range['start_time'],
        end_time=date_range['end_time'],
        report_type="Manual"
    )
    casefile_id = casefile_id_task.result()

    artifacts_task = process_attachments_task.submit(gmail_messages)
    artifacts = artifacts_task.result()

    aggregate_task = aggregate_and_save_task.submit(
        casefile_id=casefile_id,
        user_id=parameters.user_id,
        drive_files=drive_files,
        gmail_messages=gmail_messages,
        calendar_events=calendar_events,
        artifacts=artifacts,
        tag="manual-sync"
    )
    aggregate_task.result()

    logger.info("Workspace Manual Sync flow finished successfully.")
    return {"status": "success", "casefile_id": casefile_id}

# --- Local Testing Block ---
if __name__ == "__main__":
    import logging
    import asyncio
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO)

    print("--- Running Workspace Activity Report Manual Flow Local Test ---")
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found.")

    from src.core.dependencies import get_database_manager
    from src.core.models.user import UserInDB, UserRole
    from src.core.security import get_password_hash

    start_date_test = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    
    test_params = ManualWorkspaceActivityFlowParameters(
        user_id="local_test_user_manual",
        start_date=start_date_test
    )

    async def main():
        db_manager = get_database_manager()
        test_user = await db_manager.get_user_by_username(test_params.user_id)
        if not test_user:
            print(f"Creating test user '{test_params.user_id}'...")
            new_user = UserInDB(
                username=test_params.user_id,
                full_name="Local Test User Manual",
                email=f"{test_params.user_id}@example.com",
                role=UserRole.ANALYST,
                hashed_password=get_password_hash("testpassword")
            )
            await db_manager.create_user(new_user)
            print("User created.")

        print(f"Starting manual flow run for range starting {test_params.start_date}...")
        await workspace_activity_report_manual_flow(parameters=test_params)
        print("Manual flow run finished.")

    asyncio.run(main())
    print("--- End of Local Test ---")
