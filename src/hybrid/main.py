"""Local-only Python 3.11 ChatGPT and Abaqus bridge foundation."""
from __future__ import annotations

import hmac
import os
from typing import Literal

import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from src.hybrid.safety import ApprovalRegistry


app = FastAPI(title="AbaqusGPT Hybrid Local API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:8000", "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
_bearer = HTTPBearer(auto_error=False)
_registry = ApprovalRegistry()


def require_local_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    expected = os.getenv("ABAQUSGPT_API_TOKEN", "")
    if len(expected) < 32 or credentials is None or not hmac.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API token")


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    max_output_tokens: int = Field(default=800, ge=1, le=2000)


class BridgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str = Field(min_length=1, max_length=40)
    parameters: dict[StrictStr, StrictStr] = Field(max_length=12)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "local hybrid API ready"}


@app.post("/chat", dependencies=[Depends(require_local_token)])
def chat(request: ChatRequest) -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + api_key},
            json={
                "model": model,
                "messages": [message.model_dump() for message in request.messages],
                "max_tokens": request.max_output_tokens,
            },
            timeout=(5, 60),
        )
        response.raise_for_status()
        body = response.json()
        return {"answer": body["choices"][0]["message"]["content"], "model": model}
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="ChatGPT provider request failed") from exc


@app.post("/bridge/requests", dependencies=[Depends(require_local_token)])
def create_bridge_request(request: BridgeRequest) -> dict[str, object]:
    try:
        item = _registry.create(request.operation, request.parameters)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__


@app.post("/bridge/requests/{request_id}/approve", dependencies=[Depends(require_local_token)])
def approve_bridge_request(request_id: str) -> dict[str, object]:
    try:
        item = _registry.approve(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Request not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return item.__dict__


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HYBRID_API_HOST", "127.0.0.1"),
        port=int(os.getenv("HYBRID_API_PORT", "8001")),
    )

