# MDSAPP/prefect_flows/workspace_activity_report_flow.py

import os
from prefect import task, flow, get_run_logger
from pydantic import BaseModel, Field
from datetime import timedelta, datetime, timezone
from typing import Dict, Optional

# Dependency Getters
from src.core.dependencies import get_state_manager

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
class WorkspaceActivityFlowParameters(BaseModel):
    user_id: str = Field(default="prefect_user", description="The user ID to associate with the run.")
    days_back: Optional[int] = Field(default=1, description="How many days back to sync if no watermark is found.")

# --- Tasks Specific to this Flow ---

@task
async def get_sync_date_range_task(service_name: str, default_days_back: int = 1) -> Dict[str, datetime]:
    """
    Determines the date range for synchronization. It fetches the last sync time (watermark)
    and sets the start time to that value. If no watermark is found, it defaults to a
    specified number of days back. The end time is always the current time.
    """
    logger = get_run_logger()
    state_manager = get_state_manager()
    watermarks = await state_manager.get_watermarks()
    last_sync_iso = watermarks.get(f"last_{service_name}_sync")
    
    if last_sync_iso:
        start_time = datetime.fromisoformat(last_sync_iso)
        logger.info(f"Found last sync watermark for '{service_name}': {start_time.isoformat()}.")
    else:
        start_time = datetime.now(timezone.utc) - timedelta(days=default_days_back)
        logger.info(f"No watermark for '{service_name}'. Defaulting to {default_days_back} days ago: {start_time.isoformat()}.")
        
    end_time = datetime.now(timezone.utc)
    return {"start_time": start_time, "end_time": end_time}

@task
async def update_watermark_task(service_name: str, timestamp: datetime):
    """Updates the watermark in the state manager to the given timestamp."""
    logger = get_run_logger()
    state_manager = get_state_manager()
    watermark_key = f"last_{service_name}_sync"
    logger.info(f"Updating watermark for '{watermark_key}' to {timestamp.isoformat()}.")
    await state_manager.update_watermark(watermark_key, timestamp)
    logger.info("Successfully updated watermark.")

# --- Main Flow ---

@flow(name="Google Workspace Daily Sync Flow", retries=3, retry_delay_seconds=10)
async def workspace_activity_report_flow(parameters: WorkspaceActivityFlowParameters):
    logger = get_run_logger()
    logger.info(f"Starting Google Workspace Daily Sync flow for {parameters.user_id}.")

    try:
        date_range = await get_sync_date_range_task(service_name="workspace", default_days_back=parameters.days_back)

        # Concurrently fetch data from all Google Workspace services
        drive_files_task = fetch_drive_files_task.submit(date_range, task_kwargs={"retries": 3, "retry_delay_seconds": 10})
        gmail_messages_task = fetch_gmail_messages_task.submit(date_range, task_kwargs={"retries": 3, "retry_delay_seconds": 10})
        calendar_events_task = fetch_calendar_events_task.submit(date_range, task_kwargs={"retries": 3, "retry_delay_seconds": 10})

        # Wait for all fetching tasks to complete and retrieve results, handling failures
        results = await asyncio.gather(
            drive_files_task.result(raise_on_failure=True),
            gmail_messages_task.result(raise_on_failure=True),
            calendar_events_task.result(raise_on_failure=True),
            return_exceptions=True
        )

        # Unpack results, defaulting to an empty list on failure
        drive_files = results[0] if not isinstance(results[0], Exception) else []
        gmail_messages = results[1] if not isinstance(results[1], Exception) else []
        calendar_events = results[2] if not isinstance(results[2], Exception) else []

        # Log any tasks that failed
        task_names = ["Drive files", "Gmail messages", "Calendar events"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"{task_names[i]} task failed and was skipped. Error: {result}")

        if not drive_files and not gmail_messages and not calendar_events:
            logger.info("No new activity found. Flow finished.")
            await update_watermark_task.submit(service_name="workspace", timestamp=date_range['end_time'])
            logger.info("Watermark updated to current time even with no new activity.")
            return {"status": "success", "message": "No new activity."}

        casefile_id = await create_report_casefile_task.submit(
            user_id=parameters.user_id, 
            start_time=date_range['start_time'],
            end_time=date_range['end_time'],
            report_type="Automated"
        )

        artifacts = await process_attachments_task.submit(gmail_messages)

        await aggregate_and_save_task.submit(
            casefile_id=casefile_id,
            user_id=parameters.user_id,
            drive_files=drive_files,
            gmail_messages=gmail_messages,
            calendar_events=calendar_events,
            artifacts=artifacts,
            tag="automated-sync"
        )

        await update_watermark_task.submit(service_name="workspace", timestamp=date_range['end_time'])

        logger.info("Workspace Sync flow finished successfully.")
        return {"status": "success", "casefile_id": await casefile_id.result()}
    except Exception as e:
        logger.error(f"Flow failed with error: {e}", exc_info=True)
        raise

# --- Local Testing Block ---
if __name__ == "__main__":
    import logging
    import asyncio
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO)

    print("--- Running Workspace Activity Report Flow Local Test ---")
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found.")

    from src.core.dependencies import get_database_manager
    from src.core.models.user import UserInDB, UserRole
    from src.core.security import get_password_hash

    test_params = WorkspaceActivityFlowParameters(user_id="local_test_user")

    async def main():
        db_manager = get_database_manager()
        test_user = await db_manager.get_user_by_username(test_params.user_id)
        if not test_user:
            print(f"Creating test user '{test_params.user_id}'...")
            new_user = UserInDB(
                username=test_params.user_id,
                full_name="Local Test User",
                email=f"{test_params.user_id}@example.com",
                role=UserRole.ANALYST,
                hashed_password=get_password_hash("testpassword")
            )
            await db_manager.create_user(new_user)
            print("User created.")

        print("Starting flow run...")
        await workspace_activity_report_flow(parameters=test_params)
        print("Flow run finished.")

    asyncio.run(main())
    print("--- End of Local Test ---")