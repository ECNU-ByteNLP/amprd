from __future__ import annotations

import abc
import dataclasses
import time
import uuid
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class AgentMessage:
    """Canonical message exchanged between agents via the blackboard."""

    message_id: str
    timestamp: float
    sender: str
    receiver: str
    intent: str
    payload: Dict[str, Any]
    dependencies: List[str]
    status: str = "open"

    @classmethod
    def create(
        cls,
        sender: str,
        receiver: str,
        intent: str,
        payload: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> "AgentMessage":
        return cls(
            message_id=str(uuid.uuid4()),
            timestamp=time.time(),
            sender=sender,
            receiver=receiver,
            intent=intent,
            payload=payload or {},
            dependencies=dependencies or [],
            status="open",
        )


class Agent(abc.ABC):
    """Base class for all agents participating in the PRD workflow."""

    role: str

    def __init__(self, role: str) -> None:
        self.role = role

    @abc.abstractmethod
    def handle(self, message: AgentMessage, blackboard: "Blackboard") -> Optional[AgentMessage]:
        """Process an incoming message and optionally emit a response."""

    def emit(
        self,
        receiver: str,
        intent: str,
        payload: Optional[Dict[str, Any]],
        dependencies: Optional[List[str]],
    ) -> AgentMessage:
        """Helper to emit a new message."""

        return AgentMessage.create(
            sender=self.role,
            receiver=receiver,
            intent=intent,
            payload=payload,
            dependencies=dependencies,
        )


class Blackboard(abc.ABC):
    """Protocol for the shared state store orchestrating agent collaboration."""

    @abc.abstractmethod
    def post_message(self, message: AgentMessage) -> None:
        ...

    @abc.abstractmethod
    def fetch_pending(self, receiver: str) -> List[AgentMessage]:
        ...

    @abc.abstractmethod
    def update_status(self, message_id: str, status: str) -> None:
        ...

    @abc.abstractmethod
    def get_state(self) -> Dict[str, Any]:
        ...

    @abc.abstractmethod
    def update_state(self, path: List[str], value: Any) -> None:
        ...


