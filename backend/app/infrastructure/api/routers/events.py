"""SSE Events router."""
import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_db
from app.infrastructure.sse.sse_manager import SSEClient, get_sse_manager

router = APIRouter(prefix="/trivias", tags=["events"])


class CreateTicketRequest(BaseModel):
    """Request to create SSE ticket."""
    user_id: UUID | None = None


class CreateTicketResponse(BaseModel):
    """Response with SSE ticket."""
    ticket: str
    expires_in: int


@router.post("/{trivia_id}/events/token", response_model=CreateTicketResponse)
async def create_sse_ticket(
    trivia_id: UUID,
    request: CreateTicketRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a ticket for SSE connection.
    
    This endpoint allows clients to obtain a short-lived ticket that can be used
    to connect to the SSE stream. Since EventSource doesn't support custom headers,
    we use a ticket-based authentication system.
    
    Args:
        trivia_id: The trivia ID
        request: Request with optional user_id
        db: Database session (for validation)
        
    Returns:
        Ticket and expiration time
    """
    # TODO: Add authentication to verify user has access to this trivia
    # For now, we'll create the ticket without validation
    
    sse_manager = get_sse_manager()
    ticket = await sse_manager.create_ticket(trivia_id, request.user_id, expires_in_seconds=60)
    
    return CreateTicketResponse(ticket=ticket, expires_in=60)


async def generate_sse_stream(client: SSEClient):
    """
    Generate SSE stream for a client.
    
    Args:
        client: The SSEClient to stream events to
    """
    try:
        # Send initial connection event
        yield f"event: connected\n"
        yield f"data: {json.dumps({'message': 'Connected to trivia events'})}\n\n"
        
        # Stream events from queue
        while True:
            try:
                # Wait for event with timeout to allow periodic checks
                event_data = await asyncio.wait_for(client.queue.get(), timeout=30.0)
                
                event_type = event_data["event"]
                data = event_data["data"]
                
                # Format as SSE
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(data)}\n\n"
                
            except asyncio.TimeoutError:
                # Send keepalive comment
                yield ": keepalive\n\n"
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in SSE stream: {e}")
                break
                
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"SSE stream error: {e}")
    finally:
        # Cleanup: unsubscribe client
        sse_manager = get_sse_manager()
        await sse_manager.unsubscribe(client)


@router.get("/{trivia_id}/events")
async def stream_trivia_events(
    trivia_id: UUID,
    ticket: str = Query(..., description="SSE ticket obtained from /events/token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream Server-Sent Events for a trivia.
    
    This endpoint streams real-time updates about a trivia, including:
    - lobby_updated: When players join/leave/change ready status
    - admin_lobby_updated: Admin view of lobby
    - status_updated: When trivia status changes
    - current_question_updated: When current question changes
    - ranking_updated: When ranking changes
    
    Args:
        trivia_id: The trivia ID
        ticket: SSE ticket from /events/token endpoint
        db: Database session
        
    Returns:
        StreamingResponse with text/event-stream content type
    """
    # Validate ticket
    sse_manager = get_sse_manager()
    ticket_info = await sse_manager.validate_ticket(ticket)
    
    if not ticket_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired ticket",
        )
    
    ticket_trivia_id, user_id = ticket_info
    
    # Verify trivia_id matches ticket
    if ticket_trivia_id != trivia_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ticket is not valid for this trivia",
        )
    
    # Subscribe client
    client = await sse_manager.subscribe(trivia_id, user_id)
    
    # Return streaming response
    return StreamingResponse(
        generate_sse_stream(client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )

