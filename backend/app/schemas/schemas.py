from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ─── Auth ───────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be under 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, underscores, hyphens")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Repository ─────────────────────────────────────────────────────────────

class GithubUploadRequest(BaseModel):
    github_url: str
    description: Optional[str] = None

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith("https://github.com/"):
            raise ValueError("Must be a valid GitHub URL (https://github.com/owner/repo)")
        parts = v.split("/")
        if len(parts) < 5:
            raise ValueError("URL must include owner and repository name")
        return v


class RepositoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source: str
    github_url: Optional[str]
    status: str
    error_message: Optional[str]
    files_count: int
    chunks_count: int
    functions_count: int
    classes_count: int
    architecture_type: Optional[str]
    primary_language: Optional[str]
    languages: Optional[Dict[str, int]]
    architecture_summary: Optional[str]
    insights: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    repositories: List[RepositoryResponse]
    total: int


# ─── Chat ────────────────────────────────────────────────────────────────────

class CreateChatRequest(BaseModel):
    repository_id: str
    title: Optional[str] = "New Chat"


class ChatResponse(BaseModel):
    id: str
    repository_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class SourceChunk(BaseModel):
    file_path: str
    content: str
    score: float
    chunk_type: Optional[str] = None
    function_name: Optional[str] = None
    language: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    sources: Optional[List[SourceChunk]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None  # If None, creates new chat

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 5000:
            raise ValueError("Message too long (max 5000 chars)")
        return v


class ChatMessageResponse(BaseModel):
    chat_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse


# ─── Analysis ────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    repository_id: str
    query: Optional[str] = None


class FlowTraceRequest(BaseModel):
    repository_id: str
    feature: str  # e.g., "how login works"


class BugInvestigateRequest(BaseModel):
    repository_id: str
    stack_trace: str
    additional_context: Optional[str] = None


class ArchitectureResponse(BaseModel):
    repository_id: str
    architecture_type: str
    summary: str
    layers: List[Dict[str, Any]]
    patterns: List[str]
    entry_points: List[str]
    key_files: List[str]


class FlowTraceResponse(BaseModel):
    repository_id: str
    feature: str
    steps: List[Dict[str, Any]]
    files_involved: List[str]
    summary: str


class BugInvestigateResponse(BaseModel):
    repository_id: str
    probable_cause: str
    related_files: List[SourceChunk]
    root_cause_analysis: str
    suggested_fixes: List[str]


class DependencyNode(BaseModel):
    id: str
    label: str
    type: str  # file, function, class, service
    language: Optional[str] = None


class DependencyEdge(BaseModel):
    source: str
    target: str
    relationship: str  # imports, calls, extends, implements


class DependencyGraphResponse(BaseModel):
    repository_id: str
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]


class ProcessingStatusResponse(BaseModel):
    repository_id: str
    status: str
    stage: Optional[str]
    progress: float
    error: Optional[str]


class SearchRequest(BaseModel):
    repository_id: str
    query: str
    top_k: int = 10


class SearchResult(BaseModel):
    file_path: str
    content: str
    score: float
    chunk_type: Optional[str]
    function_name: Optional[str]


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
