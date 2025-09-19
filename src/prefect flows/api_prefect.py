from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from prefect.client.orchestration import get_client
import logging

router = APIRouter()

class FlowRunRequest(BaseModel):
    query: str

@router.post("/flows/run")
async def run_flow(request: FlowRunRequest):
    """
    Triggers a run of the poc_flow.
    """
    try:
        async with get_client() as client:
            deployment = await client.read_deployment_by_name("poc-flow/poc-deployment")
            flow_run = await client.create_flow_run_from_deployment(
                deployment_id=deployment.id,
                parameters={"query": request.query},
            )
            return {"message": "Flow run started.", "flow_run_id": flow_run.id.hex}
    except Exception as e:
        logging.error(f"Error in run_flow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flows/run/{flow_run_id}/status")
async def get_flow_run_status(flow_run_id: str):
    """
    Gets the status and result of a specific flow run.
    """
    try:
        async with get_client() as client:
            flow_run = await client.read_flow_run(flow_run_id)
            
            state = flow_run.state
            result = None
            if state.is_completed():
                try:
                    # state.result() will raise an exception if the flow run failed.
                    result = await state.result(fetch=True)
                except Exception:
                    # The result will be None if fetching failed.
                    pass

            return {
                "id": flow_run.id.hex,
                "name": flow_run.name,
                "status": state.name,
                "result": result,
            }
    except Exception as e:
        logging.error(f"Error in get_flow_run_status: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Flow run not found or error: {e}")
