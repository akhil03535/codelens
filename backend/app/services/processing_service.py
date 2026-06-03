import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.neo4j_service import store_file_relationships
from app.models.models import ProcessingJob, ProcessingStatus, Repository, RepositoryFile
from app.parsers.code_parser import ParsedFile, parse_file
from app.rag.embeddings import generate_embeddings
from app.rag.llm import analyze_architecture
from app.rag.vector_store import retrieve_chunks, store_chunks
from app.services.github_service import cleanup_repo, clone_github_repo, extract_zip, scan_files
from app.utils.helpers import extract_repo_name, generate_repo_id

logger = logging.getLogger(__name__)


async def _update_repo_status(
    db: AsyncSession,
    repo_id: str,
    status: ProcessingStatus,
    stage: Optional[str] = None,
    progress: float = 0.0,
    error: Optional[str] = None,
    **kwargs,
) -> None:
    repo_updates = {"status": status, **kwargs}
    await db.execute(update(Repository).where(Repository.id == repo_id).values(**repo_updates))

    job_updates: dict = {"status": status, "stage": stage, "progress": progress}
    if error:
        job_updates["error"] = error
    if status == ProcessingStatus.READY:
        job_updates["completed_at"] = datetime.now(timezone.utc)

    await db.execute(
        update(ProcessingJob)
        .where(ProcessingJob.repository_id == repo_id)
        .values(**job_updates)
    )
    await db.commit()


async def process_github_repository(
    db: AsyncSession,
    repository_id: str,
    github_url: str,
) -> None:
    """Full ingestion pipeline for a GitHub repo."""
    try:
        await _update_repo_status(db, repository_id, ProcessingStatus.CLONING, "Cloning repository", 5.0)
        repo_dir = clone_github_repo(github_url, repository_id)
        await _run_pipeline(db, repository_id, repo_dir)
    except Exception as e:
        logger.exception(f"Processing failed for {repository_id}")
        await _update_repo_status(
            db, repository_id, ProcessingStatus.FAILED,
            error=str(e)[:1000],
        )
        cleanup_repo(repository_id)


async def process_zip_repository(
    db: AsyncSession,
    repository_id: str,
    zip_bytes: bytes,
) -> None:
    """Full ingestion pipeline for a ZIP upload."""
    try:
        await _update_repo_status(db, repository_id, ProcessingStatus.CLONING, "Extracting ZIP", 5.0)
        repo_dir = extract_zip(zip_bytes, repository_id)
        await _run_pipeline(db, repository_id, repo_dir)
    except Exception as e:
        logger.exception(f"ZIP processing failed for {repository_id}")
        await _update_repo_status(
            db, repository_id, ProcessingStatus.FAILED,
            error=str(e)[:1000],
        )
        cleanup_repo(repository_id)


async def _run_pipeline(db: AsyncSession, repository_id: str, repo_dir: Path) -> None:
    try:
        # Stage 1: Scan files
        await _update_repo_status(db, repository_id, ProcessingStatus.PARSING, "Scanning files", 15.0)
        raw_files = scan_files(repo_dir)

        if not raw_files:
            raise RuntimeError("No supported source files found in repository")

        # Stage 2: Parse files
        await _update_repo_status(db, repository_id, ProcessingStatus.PARSING, "Parsing code", 30.0)
        parsed_files: List[ParsedFile] = []
        lang_counter: Counter = Counter()
        total_functions = 0
        total_classes = 0

        for file_path, content in raw_files:
            pf = parse_file(file_path, content)
            parsed_files.append(pf)
            lang_counter[pf.language] += 1
            total_functions += len(pf.functions)
            total_classes += len(pf.classes)

            # Store file record
            db_file = RepositoryFile(
                repository_id=repository_id,
                file_path=pf.file_path,
                language=pf.language,
                size_bytes=len(content.encode()),
                functions_count=len(pf.functions),
                classes_count=len(pf.classes),
                imports=pf.imports[:50],  # Cap stored imports
            )
            db.add(db_file)

        await db.commit()

        # Stage 3: Embed chunks
        await _update_repo_status(db, repository_id, ProcessingStatus.EMBEDDING, "Generating embeddings", 50.0)
        all_chunks = []
        for pf in parsed_files:
            all_chunks.extend(pf.chunks)

        if not all_chunks:
            raise RuntimeError("No code chunks generated")

        texts = []
        from app.parsers.code_parser import add_context_header
        for chunk in all_chunks:
            texts.append(add_context_header(chunk))

        embeddings = generate_embeddings(texts)
        chunks_stored = store_chunks(repository_id, all_chunks, embeddings)

        # Stage 4: Graph relationships
        await _update_repo_status(db, repository_id, ProcessingStatus.GRAPHING, "Building dependency graph", 75.0)
        store_file_relationships(repository_id, parsed_files)

        # Stage 5: Architecture analysis (non-blocking — use a sample)
        await _update_repo_status(db, repository_id, ProcessingStatus.GRAPHING, "Analyzing architecture", 85.0)
        arch_type = "unknown"
        arch_summary = ""
        try:
            sample_chunks = retrieve_chunks(
                repository_id,
                generate_embeddings(["main architecture overview entry point"])[0],
                top_k=15,
            )
            arch_json = analyze_architecture(sample_chunks)
            arch_data = json.loads(arch_json)
            arch_type = arch_data.get("architecture_type", "unknown")
            arch_summary = arch_data.get("summary", "")
        except Exception as e:
            logger.warning(f"Architecture analysis failed (non-fatal): {e}")

        primary_lang = lang_counter.most_common(1)[0][0] if lang_counter else "unknown"

        await _update_repo_status(
            db, repository_id, ProcessingStatus.READY, "Complete", 100.0,
            files_count=len(raw_files),
            chunks_count=chunks_stored,
            functions_count=total_functions,
            classes_count=total_classes,
            architecture_type=arch_type,
            architecture_summary=arch_summary,
            primary_language=primary_lang,
            languages=dict(lang_counter),
        )

        logger.info(
            f"Repository {repository_id} processed: {len(raw_files)} files, "
            f"{chunks_stored} chunks, {total_functions} functions"
        )

    finally:
        cleanup_repo(repository_id)
