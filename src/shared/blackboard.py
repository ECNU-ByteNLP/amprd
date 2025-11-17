from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents.base import AgentMessage, Blackboard


class InMemoryBlackboard(Blackboard):
    """
    Thread-safe blackboard implementation.

    Stores:
        - shared_state: Nested dictionary describing the evolving PRD draft.
        - message_queue: Pending messages per receiver.
        - history: Chronological log of all messages.
    """

    def __init__(self, persist_path: Optional[Path] = None) -> None:
        self._lock = threading.RLock()
        self._shared_state: Dict[str, Any] = {"sections": {}, "artifacts": {}, "logs": []}
        self._message_queue: Dict[str, List[AgentMessage]] = {}
        self._history: List[AgentMessage] = []
        self._persist_path = persist_path

    def post_message(self, message: AgentMessage) -> None:
        with self._lock:
            self._message_queue.setdefault(message.receiver, []).append(message)
            self._history.append(message)
            self._shared_state.setdefault("logs", []).append(
                {
                    "message_id": message.message_id,
                    "sender": message.sender,
                    "receiver": message.receiver,
                    "intent": message.intent,
                    "status": message.status,
                }
            )
            self._persist()

    def fetch_pending(self, receiver: str) -> List[AgentMessage]:
        with self._lock:
            messages = self._message_queue.get(receiver, [])
            self._message_queue[receiver] = []
            return messages

    def update_status(self, message_id: str, status: str) -> None:
        with self._lock:
            for message in self._history:
                if message.message_id == message_id:
                    message.status = status
                    break
            self._shared_state.setdefault("logs", []).append(
                {"message_id": message_id, "status": status}
            )
            self._persist()

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._shared_state)

    def update_state(self, path: List[str], value: Any) -> None:
        with self._lock:
            node = self._shared_state
            for key in path[:-1]:
                node = node.setdefault(key, {})
            node[path[-1]] = value
            self._persist()

    def _persist(self) -> None:
        if not self._persist_path:
            return
        payload = {
            "state": self._shared_state,
            "history": [message.__dict__ for message in self._history],
        }
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


