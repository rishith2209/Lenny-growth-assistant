import json
import pytest
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class AgentEventSchema(BaseModel):
    event_id: str
    session_id: str
    timestamp: str
    type: str
    model: Optional[str] = None
    provider: Optional[str] = None
    delta: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    latency_ms: Optional[int] = None
    cost_inr: Optional[float] = None


def test_pi_bridge_event_schemas():
    # 1. Test agent_started event
    raw_start = {
        "event_id": "evt_1",
        "session_id": "sess_1",
        "timestamp": "2026-09-14T12:00:00Z",
        "type": "agent_started",
        "model": "llama3.1:8b",
        "provider": "ollama",
    }
    event1 = AgentEventSchema(**raw_start)
    assert event1.type == "agent_started"

    # 2. Test text_delta event
    raw_delta = {
        "event_id": "evt_2",
        "session_id": "sess_1",
        "timestamp": "2026-09-14T12:00:01Z",
        "type": "text_delta",
        "delta": "Product-market fit is achieved when...",
    }
    event2 = AgentEventSchema(**raw_delta)
    assert event2.type == "text_delta"
    assert event2.delta is not None

    # 3. Test tool_started event
    raw_tool = {
        "event_id": "evt_3",
        "session_id": "sess_1",
        "timestamp": "2026-09-14T12:00:02Z",
        "type": "tool_started",
        "tool_call_id": "call_123",
        "tool_name": "retrieve_knowledge_test",
        "arguments": {"query": "retention"},
    }
    event3 = AgentEventSchema(**raw_tool)
    assert event3.type == "tool_started"
    assert event3.tool_name == "retrieve_knowledge_test"

    # 4. Test agent_completed event
    raw_done = {
        "event_id": "evt_4",
        "session_id": "sess_1",
        "timestamp": "2026-09-14T12:00:05Z",
        "type": "agent_completed",
        "latency_ms": 3200,
        "cost_inr": 0.0,
    }
    event4 = AgentEventSchema(**raw_done)
    assert event4.type == "agent_completed"
    assert event4.cost_inr == 0.0
