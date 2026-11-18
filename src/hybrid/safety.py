"""Bounded bridge request validation and in-memory approval state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import secrets


OPERATIONS = {
    "inspect_model": frozenset({"model_name"}),
    "read_job_status": frozenset({"job_name"}),
    "propose_model_change": frozenset({"model_name", "change_type", "description"}),
    "submit_job": frozenset({"job_name"}),
}
APPROVAL_REQUIRED = frozenset({"propose_model_change", "submit_job"})
MAX_PARAMETERS = 12
MAX_VALUE_LENGTH = 2048


def validate_bridge_request(operation: str, parameters: Any) -> dict[str, str]:
    """Accept only named operations and scalar, bounded, operation-specific fields."""
    if operation not in OPERATIONS:
        raise ValueError("operation is not allowlisted")
    if not isinstance(parameters, dict) or len(parameters) > MAX_PARAMETERS:
        raise ValueError("parameters must be a small object")
    allowed = OPERATIONS[operation]
    if set(parameters) != allowed:
        raise ValueError("parameters do not match the operation schema")
    result: dict[str, str] = {}
    for key, value in parameters.items():
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_VALUE_LENGTH:
            raise ValueError("parameter values must be non-empty bounded strings")
        if "\x00" in value:
            raise ValueError("NUL bytes are not allowed")
        result[key] = value.strip()
    return result


@dataclass
class PendingRequest:
    request_id: str
    operation: str
    parameters: dict[str, str]
    status: str
    approval_required: bool


class ApprovalRegistry:
    """Process-local request registry. Approval never invokes an executor."""

    def __init__(self) -> None:
        self._items: dict[str, PendingRequest] = {}

    def create(self, operation: str, parameters: Any) -> PendingRequest:
        clean = validate_bridge_request(operation, parameters)
        request_id = secrets.token_urlsafe(18)
        required = operation in APPROVAL_REQUIRED
        item = PendingRequest(
            request_id=request_id,
            operation=operation,
            parameters=clean,
            status="awaiting_approval" if required else "queued_read_only",
            approval_required=required,
        )
        self._items[request_id] = item
        return item

    def approve(self, request_id: str) -> PendingRequest:
        item = self._items.get(request_id)
        if item is None:
            raise KeyError("request not found")
        if not item.approval_required or item.status != "awaiting_approval":
            raise ValueError("request is not awaiting approval")
        # Deliberately does not execute or submit anything.
        item.status = "approved_for_operator_review"
        return item

