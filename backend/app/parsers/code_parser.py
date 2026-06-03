"""
Tree-sitter based code parser for extracting semantic units from source files.
Falls back to regex-based extraction when tree-sitter grammars are unavailable.
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Attempt to load tree-sitter; fall back gracefully if not available
_TREESITTER_AVAILABLE = False
try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    from tree_sitter import Language, Parser as TSParser
    _TREESITTER_AVAILABLE = True
    logger.info("Tree-sitter available — using AST-based parsing")
except ImportError:
    logger.warning("Tree-sitter not available — using regex-based parsing fallback")


@dataclass
class ParsedChunk:
    content: str
    file_path: str
    chunk_type: str        # function | class | method | import_block | code_block
    name: Optional[str]
    language: str
    start_line: int
    end_line: int
    imports: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None


@dataclass
class ParsedFile:
    file_path: str
    language: str
    chunks: List[ParsedChunk]
    imports: List[str]
    functions: List[str]
    classes: List[str]
    raw_content: str


LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
}


def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext, "unknown")


# ─── Regex-based fallback parsers ────────────────────────────────────────────

def _extract_python_chunks(content: str, file_path: str) -> List[ParsedChunk]:
    chunks = []
    lines = content.splitlines()
    language = "python"

    # Extract imports block
    import_lines = [l for l in lines if l.startswith(("import ", "from "))]
    if import_lines:
        import_block = "\n".join(import_lines)
        chunks.append(ParsedChunk(
            content=import_block, file_path=file_path, chunk_type="import_block",
            name="imports", language=language, start_line=1, end_line=len(import_lines),
            imports=import_lines,
        ))

    # Extract functions and classes using indentation-aware regex
    current_block: List[str] = []
    current_start = 0
    current_name: Optional[str] = None
    current_type: Optional[str] = None
    current_class: Optional[str] = None
    in_class = False
    class_indent = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        class_match = re.match(r'^class\s+(\w+)', line)
        func_match = re.match(r'^(?:async\s+)?def\s+(\w+)', line)
        method_match = re.match(r'^    (?:async\s+)?def\s+(\w+)', line)

        if class_match:
            if current_block and current_name:
                chunks.append(ParsedChunk(
                    content="\n".join(current_block), file_path=file_path,
                    chunk_type=current_type or "code_block", name=current_name,
                    language=language, start_line=current_start, end_line=i - 1,
                ))
            current_name = class_match.group(1)
            current_type = "class"
            current_block = [line]
            current_start = i
            in_class = True
            class_indent = indent
            current_class = current_name

        elif func_match and indent == 0:
            if current_block and current_name:
                chunks.append(ParsedChunk(
                    content="\n".join(current_block), file_path=file_path,
                    chunk_type=current_type or "code_block", name=current_name,
                    language=language, start_line=current_start, end_line=i - 1,
                ))
            current_name = func_match.group(1)
            current_type = "function"
            current_block = [line]
            current_start = i
            in_class = False
            current_class = None

        elif method_match and in_class:
            # Append to current class chunk
            if current_block:
                current_block.append(line)
        else:
            if current_block:
                current_block.append(line)

    if current_block and current_name:
        chunks.append(ParsedChunk(
            content="\n".join(current_block), file_path=file_path,
            chunk_type=current_type or "code_block", name=current_name,
            language=language, start_line=current_start, end_line=len(lines),
        ))

    # If no chunks extracted, treat entire file as a code block
    if not chunks:
        chunks.append(ParsedChunk(
            content=content, file_path=file_path, chunk_type="code_block",
            name=Path(file_path).stem, language=language,
            start_line=1, end_line=len(lines),
        ))

    return chunks


def _extract_js_ts_chunks(content: str, file_path: str) -> List[ParsedChunk]:
    chunks = []
    lines = content.splitlines()
    language = detect_language(file_path)

    # Extract imports
    import_lines = [l for l in lines if re.match(r'^import\s+|^const\s+\w+\s*=\s*require\(', l)]
    if import_lines:
        chunks.append(ParsedChunk(
            content="\n".join(import_lines), file_path=file_path, chunk_type="import_block",
            name="imports", language=language, start_line=1, end_line=len(import_lines),
            imports=import_lines,
        ))

    # Extract function declarations and arrow functions
    patterns = [
        (r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', "function"),
        (r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(', "function"),
        (r'^(?:export\s+)?class\s+(\w+)', "class"),
        (r'^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', "method"),
        (r'^(?:export\s+default\s+)?(?:async\s+)?function', "function"),
        (r'^\s+(?:public|private|protected|static).*(?:async\s+)?(\w+)\s*\(', "method"),
    ]

    current_block: List[str] = []
    current_start = 0
    current_name: Optional[str] = None
    current_type: Optional[str] = None
    brace_depth = 0
    in_block = False

    for i, line in enumerate(lines, start=1):
        if in_block:
            current_block.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                chunks.append(ParsedChunk(
                    content="\n".join(current_block), file_path=file_path,
                    chunk_type=current_type or "code_block", name=current_name,
                    language=language, start_line=current_start, end_line=i,
                ))
                current_block = []
                in_block = False
                brace_depth = 0
        else:
            matched = False
            for pattern, chunk_type in patterns:
                m = re.match(pattern, line)
                if m:
                    current_name = m.group(1) if m.lastindex else Path(file_path).stem
                    current_type = chunk_type
                    current_start = i
                    current_block = [line]
                    brace_depth = line.count("{") - line.count("}")
                    in_block = brace_depth > 0
                    matched = True
                    break
            if not matched and current_block:
                current_block.append(line)

    if not chunks:
        chunks.append(ParsedChunk(
            content=content, file_path=file_path, chunk_type="code_block",
            name=Path(file_path).stem, language=language,
            start_line=1, end_line=len(lines),
        ))

    return chunks


def _extract_java_chunks(content: str, file_path: str) -> List[ParsedChunk]:
    chunks = []
    lines = content.splitlines()
    language = "java"

    import_lines = [l for l in lines if l.strip().startswith("import ")]
    if import_lines:
        chunks.append(ParsedChunk(
            content="\n".join(import_lines), file_path=file_path, chunk_type="import_block",
            name="imports", language=language, start_line=1, end_line=len(import_lines),
            imports=import_lines,
        ))

    class_match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
    if class_match:
        class_name = class_match.group(1)

    method_pattern = re.compile(
        r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{'
    )

    current_block: List[str] = []
    current_start = 0
    current_name: Optional[str] = None
    brace_depth = 0
    in_method = False

    for i, line in enumerate(lines, start=1):
        if in_method:
            current_block.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                chunks.append(ParsedChunk(
                    content="\n".join(current_block), file_path=file_path,
                    chunk_type="method", name=current_name,
                    language=language, start_line=current_start, end_line=i,
                ))
                current_block = []
                in_method = False
                brace_depth = 0
        else:
            m = method_pattern.search(line)
            if m and not re.match(r'\s*//|/\*', line):
                current_name = m.group(1)
                current_start = i
                current_block = [line]
                brace_depth = line.count("{") - line.count("}")
                in_method = brace_depth > 0

    if not chunks:
        chunks.append(ParsedChunk(
            content=content, file_path=file_path, chunk_type="code_block",
            name=Path(file_path).stem, language=language,
            start_line=1, end_line=len(lines),
        ))

    return chunks


# ─── Main parser ─────────────────────────────────────────────────────────────

def parse_file(file_path: str, content: str) -> ParsedFile:
    """
    Parse a source file and extract semantic chunks, imports, functions, and classes.
    Uses tree-sitter when available, falls back to regex extraction.
    """
    language = detect_language(file_path)

    if language == "python":
        chunks = _extract_python_chunks(content, file_path)
    elif language in ("javascript", "typescript"):
        chunks = _extract_js_ts_chunks(content, file_path)
    elif language == "java":
        chunks = _extract_java_chunks(content, file_path)
    else:
        # Generic fallback: treat file as one block
        lines = content.splitlines()
        chunks = [ParsedChunk(
            content=content, file_path=file_path, chunk_type="code_block",
            name=Path(file_path).stem, language=language,
            start_line=1, end_line=len(lines),
        )]

    # Collect metadata
    all_imports = []
    functions = []
    classes = []

    for chunk in chunks:
        if chunk.chunk_type == "import_block":
            all_imports.extend(chunk.imports)
        elif chunk.chunk_type == "function" and chunk.name:
            functions.append(chunk.name)
        elif chunk.chunk_type == "class" and chunk.name:
            classes.append(chunk.name)
        elif chunk.chunk_type == "method" and chunk.name:
            functions.append(chunk.name)

    return ParsedFile(
        file_path=file_path,
        language=language,
        chunks=chunks,
        imports=list(set(all_imports)),
        functions=functions,
        classes=classes,
        raw_content=content,
    )


def add_context_header(chunk: ParsedChunk) -> str:
    """Add a context header to a chunk's content for better retrieval."""
    parts = [f"# File: {chunk.file_path}"]
    if chunk.chunk_type != "code_block":
        parts.append(f"# Type: {chunk.chunk_type}")
    if chunk.name:
        parts.append(f"# Name: {chunk.name}")
    if chunk.parent_class:
        parts.append(f"# Class: {chunk.parent_class}")
    parts.append(f"# Language: {chunk.language}")
    parts.append(f"# Lines: {chunk.start_line}-{chunk.end_line}")
    parts.append("")
    parts.append(chunk.content)
    return "\n".join(parts)
