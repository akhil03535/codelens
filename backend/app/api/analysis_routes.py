import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_current_active_user
from app.database.session import get_db
from app.graph.neo4j_service import get_dependency_graph
from app.models.models import ProcessingStatus, Repository, RepositoryFile, User
from app.rag.embeddings import generate_single_embedding
from app.rag.llm import (
    generate_documentation, generate_onboarding,
    investigate_bug, trace_flow,
)
from app.rag.vector_store import retrieve_chunks
from app.schemas.schemas import (
    AnalysisRequest, ArchitectureResponse, BugInvestigateRequest,
    BugInvestigateResponse, DependencyEdge, DependencyGraphResponse,
    DependencyNode, FlowTraceRequest, FlowTraceResponse,
    SearchRequest, SearchResponse, SearchResult, SourceChunk,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])


async def _get_ready_repo(repo_id: str, user_id: str, db: AsyncSession) -> Repository:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")
    if repo.status != ProcessingStatus.READY:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Repository not ready (status: {repo.status.value})"
        )
    return repo


@router.post("/architecture", response_model=ArchitectureResponse)
async def get_architecture(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    repo = await _get_ready_repo(req.repository_id, user.id, db)

    # Return cached analysis if available
    if repo.architecture_summary and repo.architecture_type and repo.architecture_type != "unknown":
        return ArchitectureResponse(
            repository_id=req.repository_id,
            architecture_type=repo.architecture_type,
            summary=repo.architecture_summary,
            layers=[],
            patterns=[],
            entry_points=[],
            key_files=[],
        )

    # Run fresh analysis
    query_emb = generate_single_embedding("main architecture overview entry points services controllers")
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=15)

    from app.rag.llm import analyze_architecture
    raw = analyze_architecture(chunks)
    data = json.loads(raw)

    return ArchitectureResponse(
        repository_id=req.repository_id,
        architecture_type=data.get("architecture_type", "unknown"),
        summary=data.get("summary", ""),
        layers=data.get("layers", []),
        patterns=data.get("patterns", []),
        entry_points=data.get("entry_points", []),
        key_files=data.get("key_files", []),
    )


@router.post("/flow", response_model=FlowTraceResponse)
async def trace_code_flow(
    req: FlowTraceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await _get_ready_repo(req.repository_id, user.id, db)

    query_emb = generate_single_embedding(req.feature)
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=10)

    raw = trace_flow(req.feature, chunks)
    data = json.loads(raw)

    return FlowTraceResponse(
        repository_id=req.repository_id,
        feature=req.feature,
        steps=data.get("steps", []),
        files_involved=data.get("files_involved", []),
        summary=data.get("summary", ""),
    )


@router.post("/bug", response_model=BugInvestigateResponse)
async def investigate_bug_report(
    req: BugInvestigateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await _get_ready_repo(req.repository_id, user.id, db)

    # Search for relevant chunks using the stack trace as query
    query = f"{req.stack_trace[:500]} {req.additional_context or ''}"
    query_emb = generate_single_embedding(query)
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=8)

    raw = investigate_bug(req.stack_trace, chunks, req.additional_context or "")
    data = json.loads(raw)

    related = [
        SourceChunk(
            file_path=c["file_path"],
            content=c["content"][:500],
            score=c["score"],
            chunk_type=c.get("chunk_type"),
            function_name=c.get("function_name"),
            language=c.get("language"),
        )
        for c in chunks[:5]
    ]

    return BugInvestigateResponse(
        repository_id=req.repository_id,
        probable_cause=data.get("probable_cause", ""),
        related_files=related,
        root_cause_analysis=data.get("root_cause_analysis", ""),
        suggested_fixes=data.get("suggested_fixes", []),
    )


@router.post("/documentation")
async def generate_docs(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    repo = await _get_ready_repo(req.repository_id, user.id, db)

    query_emb = generate_single_embedding("overview architecture setup usage getting started")
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=20)
    docs = generate_documentation(chunks, repo.name)

    return {"repository_id": req.repository_id, "documentation": docs, "format": "markdown"}


@router.post("/onboarding")
async def get_onboarding(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    repo = await _get_ready_repo(req.repository_id, user.id, db)

    query_emb = generate_single_embedding("main entry point getting started setup configuration")
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=12)
    raw = generate_onboarding(chunks, repo.name)
    data = json.loads(raw)

    return {"repository_id": req.repository_id, **data}


@router.get("/graph/{repository_id}", response_model=DependencyGraphResponse)
async def get_dependency_graph_route(
    repository_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    repo = await _get_ready_repo(repository_id, user.id, db)

    # Try Neo4j first
    graph = get_dependency_graph(repository_id)

    # Fallback: build graph from database files
    if not graph["nodes"]:
        result = await db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repository_id).limit(80)
        )
        files = result.scalars().all()

        nodes = [
            DependencyNode(
                id=f.file_path,
                label=f.file_path.split("/")[-1],
                type="file",
                language=f.language,
            )
            for f in files
        ]

        # Build edges from import data
        edges = []
        file_stems = {f.file_path.split("/")[-1].rsplit(".", 1)[0]: f.file_path for f in files}

        for f in files:
            if f.imports:
                for imp in f.imports:
                    parts = imp.replace("from ", "").replace("import ", "").strip().split()[0]
                    stem = parts.split(".")[-1].strip("'\"")
                    if stem in file_stems and file_stems[stem] != f.file_path:
                        edges.append(DependencyEdge(
                            source=f.file_path,
                            target=file_stems[stem],
                            relationship="imports",
                        ))

        return DependencyGraphResponse(
            repository_id=repository_id,
            nodes=nodes,
            edges=edges,
        )

    return DependencyGraphResponse(
        repository_id=repository_id,
        nodes=[DependencyNode(**n) for n in graph["nodes"]],
        edges=[DependencyEdge(**e) for e in graph["edges"]],
    )


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await _get_ready_repo(req.repository_id, user.id, db)

    query_emb = generate_single_embedding(req.query)
    chunks = retrieve_chunks(req.repository_id, query_emb, top_k=min(req.top_k, 20))

    results = [
        SearchResult(
            file_path=c["file_path"],
            content=c["content"][:800],
            score=c["score"],
            chunk_type=c.get("chunk_type"),
            function_name=c.get("function_name"),
        )
        for c in chunks
    ]

    return SearchResponse(results=results, query=req.query)
