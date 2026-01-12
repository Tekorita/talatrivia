"""SSE Manager for broadcasting events to connected clients."""
import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict
from uuid import UUID

logger = logging.getLogger(__name__)


class SSEClient:
    """Represents a single SSE client connection."""

    def __init__(self, trivia_id: UUID, user_id: UUID | None = None):
        self.trivia_id = trivia_id
        self.user_id = user_id
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.created_at = datetime.now(UTC)

    async def send(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event to this client."""
        await self.queue.put({"event": event_type, "data": data})


class SSEManager:
    """
    In-memory SSE Manager for broadcasting events to connected clients.
    
    Manages subscribers per trivia using asyncio.Queue.
    """

    def __init__(self):
        # Map: trivia_id -> set of SSEClient
        self._clients: Dict[UUID, set[SSEClient]] = {}
        # Map: ticket -> (trivia_id, user_id, expires_at)
        self._tickets: Dict[str, tuple[UUID, UUID | None, datetime]] = {}
        self._lock = asyncio.Lock()

    async def create_ticket(
        self, trivia_id: UUID, user_id: UUID | None = None, expires_in_seconds: int = 60
    ) -> str:
        """
        Create a ticket for SSE connection.
        
        Args:
            trivia_id: The trivia ID
            user_id: Optional user ID
            expires_in_seconds: Ticket expiration time (default 60s)
            
        Returns:
            Ticket string
        """
        ticket = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)
        
        async with self._lock:
            self._tickets[ticket] = (trivia_id, user_id, expires_at)
        
        logger.info(f"Created SSE ticket for trivia {trivia_id}, user {user_id}, expires at {expires_at}")
        return ticket

    async def validate_ticket(self, ticket: str) -> tuple[UUID, UUID | None] | None:
        """
        Validate a ticket and return trivia_id and user_id.
        
        Args:
            ticket: The ticket to validate
            
        Returns:
            Tuple of (trivia_id, user_id) if valid, None otherwise
        """
        async with self._lock:
            if ticket not in self._tickets:
                return None
            
            trivia_id, user_id, expires_at = self._tickets[ticket]
            
            # Check expiration
            if datetime.now(UTC) > expires_at:
                del self._tickets[ticket]
                logger.warning(f"Ticket {ticket[:8]}... expired")
                return None
            
            return trivia_id, user_id

    async def subscribe(self, trivia_id: UUID, user_id: UUID | None = None) -> SSEClient:
        """
        Subscribe a client to trivia events.
        
        Args:
            trivia_id: The trivia ID
            user_id: Optional user ID
            
        Returns:
            SSEClient instance
        """
        client = SSEClient(trivia_id, user_id)
        
        async with self._lock:
            if trivia_id not in self._clients:
                self._clients[trivia_id] = set()
            self._clients[trivia_id].add(client)
        
        logger.info(f"Client subscribed to trivia {trivia_id} (total clients: {len(self._clients.get(trivia_id, set()))})")
        return client

    async def unsubscribe(self, client: SSEClient) -> None:
        """
        Unsubscribe a client from trivia events.
        
        Args:
            client: The SSEClient to unsubscribe
        """
        async with self._lock:
            if client.trivia_id in self._clients:
                self._clients[client.trivia_id].discard(client)
                # Clean up empty trivia sets
                if not self._clients[client.trivia_id]:
                    del self._clients[client.trivia_id]
        
        logger.info(f"Client unsubscribed from trivia {client.trivia_id}")

    async def broadcast(
        self, trivia_id: UUID, event_type: str, data: Dict[str, Any]
    ) -> None:
        """
        Broadcast an event to all clients subscribed to a trivia.
        
        Args:
            trivia_id: The trivia ID
            event_type: The event type (e.g., "lobby_updated")
            data: The event data (will be JSON serialized)
        """
        async with self._lock:
            clients = self._clients.get(trivia_id, set()).copy()
        
        if not clients:
            logger.debug(f"No clients subscribed to trivia {trivia_id} for event {event_type}")
            return
        
        # Send to all clients
        dead_clients = []
        for client in clients:
            try:
                await client.send(event_type, data)
            except Exception as e:
                logger.warning(f"Error sending event to client: {e}")
                dead_clients.append(client)
        
        # Remove dead clients
        if dead_clients:
            async with self._lock:
                for dead_client in dead_clients:
                    if dead_client.trivia_id in self._clients:
                        self._clients[dead_client.trivia_id].discard(dead_client)
                        if not self._clients[dead_client.trivia_id]:
                            del self._clients[dead_client.trivia_id]
        
        logger.info(f"Broadcasted {event_type} to {len(clients) - len(dead_clients)} clients for trivia {trivia_id}")

    async def cleanup_expired_tickets(self) -> None:
        """Remove expired tickets (should be called periodically)."""
        now = datetime.now(UTC)
        async with self._lock:
            expired_tickets = [
                ticket
                for ticket, (_, _, expires_at) in self._tickets.items()
                if now > expires_at
            ]
            for ticket in expired_tickets:
                del self._tickets[ticket]
        
        if expired_tickets:
            logger.debug(f"Cleaned up {len(expired_tickets)} expired tickets")


# Global SSE Manager instance
_sse_manager: SSEManager | None = None


def get_sse_manager() -> SSEManager:
    """Get the global SSE Manager instance."""
    global _sse_manager
    if _sse_manager is None:
        _sse_manager = SSEManager()
    return _sse_manager

