"""Pydantic models for API"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Message(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class QuestionRequest(BaseModel):
    """Request model for asking a question"""
    question: str = Field(..., description="User question about Abaqus")
    top_k: Optional[int] = Field(3, description="Number of documents to retrieve (default: 3 for speed)")
    temperature: Optional[float] = Field(0.2, description="LLM temperature (default: 0.2 for focused answers)")
    conversation_history: Optional[List[Message]] = Field([], description="Previous conversation for context")


class Source(BaseModel):
    """Source document information"""
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")


class AnswerResponse(BaseModel):
    """Response model for answers"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(..., description="Source documents used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To define material properties in Abaqus, you use the *MATERIAL keyword...",
                "sources": [
                    {
                        "title": "Abaqus Keywords Reference Guide - Material Definition",
                        "url": "http://130.149.89.49:2080/v2016/books/usb/default.htm"
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    vector_store_count: int = Field(..., description="Number of documents in vector store")
    ollama_available: bool = Field(..., description="Whether Ollama is available")
