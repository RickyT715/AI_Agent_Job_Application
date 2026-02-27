"""Browser agent API and WebSocket endpoints."""

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from app.core.rate_limit import limiter
from app.core.websocket import manager
from app.schemas.api import (
    AgentResumeRequest,
    AgentStartRequest,
    TaskStatusResponse,
)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/start", response_model=TaskStatusResponse)
@limiter.limit("10/minute")
async def start_agent(request: Request, request_body: AgentStartRequest):
    """Start the browser agent for a job application.

    Enqueues an ARQ task and returns a task/thread ID for tracking.
    """
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is None:
        raise HTTPException(status_code=503, detail="Task queue unavailable")

    job = await arq_pool.enqueue_job(
        "run_agent",
        job_id=request_body.job_id,
    )
    return TaskStatusResponse(task_id=job.job_id, status="queued")


@router.post("/resume/{thread_id}", response_model=TaskStatusResponse)
async def resume_agent(thread_id: str, request: AgentResumeRequest):
    """Resume an interrupted agent with a human decision.

    Actions: approve, reject, edit
    """
    # TODO: Resume LangGraph with the decision
    return TaskStatusResponse(
        task_id=thread_id,
        status="running",
        result={"action": request.action},
    )


@router.websocket("/ws/agent-status")
async def agent_status_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time agent progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for client messages
            await websocket.receive_text()
            # Client can send pings or commands
    except WebSocketDisconnect:
        manager.disconnect(websocket)
