import logging
import time
from typing import AsyncGenerator, Dict, List, Optional

import requests

from app.config.settings import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CodeLens AI — an expert software engineer assistant specializing in codebase analysis.

RULES:
1. Answer ONLY from the provided code context. Never fabricate code, function names, or behavior.
2. Always cite file paths and line numbers when referencing code.
3. If the answer isn't in the context, say: "I couldn't find this in the indexed codebase."
4. Be precise and technical. Developers are your audience.
5. When explaining flows, trace them step by step through the actual files.
6. Format code snippets with proper markdown code blocks with language tags.
"""

ARCHITECTURE_PROMPT = """You are an expert software architect analyzing a codebase.

Analyze the provided code context and identify:
1. Overall architecture pattern (MVC, layered, microservices, monolith, etc.)
2. Key layers and their responsibilities
3. Design patterns in use (Repository, Factory, Observer, etc.)
4. Entry points (main files, API routers, index files)
5. Core services and their roles

Respond in structured JSON format:
{
  "architecture_type": "...",
  "summary": "...",
  "layers": [{"name": "...", "description": "...", "files": [...]}],
  "patterns": [...],
  "entry_points": [...],
  "key_files": [...]
}
"""

FLOW_TRACE_PROMPT = """You are tracing a code flow through a codebase.

Given the code context, trace the complete execution flow for the requested feature.
Show each step from entry point to completion, referencing actual files and functions.

Respond in JSON:
{
  "steps": [
    {"step": 1, "description": "...", "file": "...", "function": "...", "details": "..."}
  ],
  "files_involved": [...],
  "summary": "..."
}
"""

BUG_PROMPT = """You are an expert debugger analyzing a bug report against a codebase.

Given the stack trace and relevant code, provide:
1. Probable root cause
2. Exact location in code
3. Root cause analysis
4. Concrete fix suggestions

Respond in JSON:
{
  "probable_cause": "...",
  "root_cause_analysis": "...",
  "suggested_fixes": [...]
}
"""

DOC_PROMPT = """You are a technical documentation expert.

Generate comprehensive documentation for this codebase including:
1. Overview and purpose
2. Architecture explanation
3. Key components and their roles
4. API endpoints (if any)
5. Setup and usage instructions
6. Developer onboarding guide

Use clear markdown formatting with headers, code examples, and explanations.
"""


def _call_groq(
    messages: List[Dict],
    system: str = SYSTEM_PROMPT,
    temperature: float = 0.1,
    max_retries: int = settings.GROQ_MAX_RETRIES,
    json_mode: bool = False,
) -> str:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")

    payload: Dict = {
        "model": settings.GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": settings.GROQ_MAX_TOKENS,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                settings.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=settings.GROQ_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Empty choices in Groq response")
            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                raise ValueError("Empty content in Groq response")
            return content

        except requests.Timeout:
            last_error = requests.RequestException(f"Groq timeout after {settings.GROQ_TIMEOUT}s")
        except requests.HTTPError as e:
            body = ""
            try:
                body = resp.json().get("error", {}).get("message", "")
            except Exception:
                pass
            last_error = requests.RequestException(f"Groq HTTP {resp.status_code}: {body or str(e)}")
            if resp.status_code in (400, 401, 403):
                break  # Don't retry auth errors
        except Exception as e:
            last_error = e

        if attempt < max_retries - 1:
            wait = 2 ** attempt
            logger.warning(f"Groq attempt {attempt + 1} failed, retrying in {wait}s: {last_error}")
            time.sleep(wait)

    raise last_error or RuntimeError("All Groq retries failed")


def build_rag_messages(question: str, chunks: List[Dict]) -> List[Dict]:
    if not chunks:
        ctx = "No relevant code context found."
    else:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"--- Source {i} (file: {c['file_path']}, type: {c.get('chunk_type','')}, "
                f"score: {c['score']:.3f}) ---\n{c['content']}"
            )
        ctx = "\n\n".join(parts)

    return [{"role": "user", "content": f"CODE CONTEXT:\n{ctx}\n\nQUESTION:\n{question}"}]


def generate_chat_answer(question: str, chunks: List[Dict]) -> str:
    messages = build_rag_messages(question, chunks)
    return _call_groq(messages)


def analyze_architecture(chunks: List[Dict]) -> str:
    ctx = "\n\n".join(
        f"--- {c['file_path']} ---\n{c['content']}" for c in chunks[:20]
    )
    messages = [{"role": "user", "content": f"Analyze this codebase:\n\n{ctx}"}]
    return _call_groq(messages, system=ARCHITECTURE_PROMPT, json_mode=True)


def trace_flow(feature: str, chunks: List[Dict]) -> str:
    ctx = "\n\n".join(f"--- {c['file_path']} ---\n{c['content']}" for c in chunks)
    messages = [{"role": "user", "content": f"Trace the flow for: {feature}\n\nCode:\n{ctx}"}]
    return _call_groq(messages, system=FLOW_TRACE_PROMPT, json_mode=True)


def investigate_bug(stack_trace: str, chunks: List[Dict], context: str = "") -> str:
    ctx = "\n\n".join(f"--- {c['file_path']} ---\n{c['content']}" for c in chunks)
    user_content = f"STACK TRACE:\n{stack_trace}\n\nADDITIONAL CONTEXT:\n{context}\n\nCODE:\n{ctx}"
    messages = [{"role": "user", "content": user_content}]
    return _call_groq(messages, system=BUG_PROMPT, json_mode=True)


def generate_documentation(chunks: List[Dict], repo_name: str) -> str:
    ctx = "\n\n".join(f"--- {c['file_path']} ---\n{c['content']}" for c in chunks[:25])
    messages = [{"role": "user", "content": f"Repository: {repo_name}\n\nCode:\n{ctx}"}]
    return _call_groq(messages, system=DOC_PROMPT, temperature=0.3)


def generate_onboarding(chunks: List[Dict], repo_name: str) -> str:
    ctx = "\n\n".join(f"--- {c['file_path']} ---\n{c['content']}" for c in chunks[:15])
    system = """Generate a developer onboarding guide in JSON:
{
  "overview": "...",
  "learning_roadmap": [{"step": 1, "title": "...", "description": "...", "files_to_read": [...]}],
  "important_files": [{"path": "...", "purpose": "..."}],
  "architecture_walkthrough": "...",
  "setup_notes": "..."
}"""
    messages = [{"role": "user", "content": f"Repository: {repo_name}\n\nCode:\n{ctx}"}]
    return _call_groq(messages, system=system, json_mode=True)
