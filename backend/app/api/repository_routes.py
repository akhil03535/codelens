import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_current_active_user
from app.database.session import get_db
from app.models.models import (
    ProcessingJob, ProcessingStatus, Repository, RepositoryFile, RepositorySource,
)
from app.rag.vector_store import delete_collection
from app.schemas.schemas import (
    GithubUploadRequest, ProcessingStatusResponse,
    RepositoryListResponse, RepositoryResponse,
)
from app.services.processing_service import process_github_repository, process_zip_repository
from app.models.models import User
from app.utils.helpers import extract_repo_name, generate_repo_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/repositories", tags=["Repositories"])


def _to_response(repo: Repository) -> RepositoryResponse:
    return RepositoryResponse.model_validate(repo)


@router.post("/github", response_model=RepositoryResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_github(
    req: GithubUploadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    repo_name = extract_repo_name(req.github_url)
    repo_id = str(uuid.uuid4())

    repo = Repository(
        id=repo_id,
        user_id=user.id,
        name=repo_name,
        description=req.description,
        source=RepositorySource.GITHUB,
        github_url=req.github_url,
        status=ProcessingStatus.PENDING,
    )
    db.add(repo)

    job = ProcessingJob(repository_id=repo_id, status=ProcessingStatus.PENDING, progress=0.0)
    db.add(job)
    await db.commit()
    await db.refresh(repo)

    background_tasks.add_task(process_github_repository, db, repo_id, req.github_url)
    return _to_response(repo)


@router.post("/zip", response_model=RepositoryResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only .zip files are supported")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > 100:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"ZIP too large ({size_mb:.1f}MB, max 100MB)")

    repo_name = file.filename.replace(".zip", "")
    repo_id = str(uuid.uuid4())

    repo = Repository(
        id=repo_id,
        user_id=user.id,
        name=repo_name,
        source=RepositorySource.ZIP,
        status=ProcessingStatus.PENDING,
    )
    db.add(repo)
    job = ProcessingJob(repository_id=repo_id, status=ProcessingStatus.PENDING, progress=0.0)
    db.add(job)
    await db.commit()
    await db.refresh(repo)

    background_tasks.add_task(process_zip_repository, db, repo_id, contents)
    return _to_response(repo)


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user.id)
        .order_by(Repository.created_at.desc())
    )
    repos = result.scalars().all()
    return RepositoryListResponse(
        repositories=[_to_response(r) for r in repos],
        total=len(repos),
    )


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")
    return _to_response(repo)


@router.get("/{repo_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    job_result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.repository_id == repo_id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(1)
    )
    job = job_result.scalar_one_or_none()

    return ProcessingStatusResponse(
        repository_id=repo_id,
        status=repo.status.value,
        stage=job.stage if job else None,
        progress=job.progress if job else 0.0,
        error=repo.error_message,
    )


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    delete_collection(repo_id)
    await db.delete(repo)
    await db.commit()
