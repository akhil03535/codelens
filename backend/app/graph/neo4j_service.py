"""
Neo4j graph service for storing and querying code relationships.
Gracefully disabled when Neo4j is not configured.
"""
import logging
from typing import Dict, List, Optional

from app.config.settings import settings
from app.parsers.code_parser import ParsedFile

logger = logging.getLogger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is None and settings.NEO4J_ENABLED:
        try:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            _driver.verify_connectivity()
            logger.info("Neo4j connected")
        except Exception as e:
            logger.warning(f"Neo4j not available: {e}. Graph features disabled.")
            settings.NEO4J_ENABLED = False
    return _driver


def store_file_relationships(repo_id: str, parsed_files: List[ParsedFile]) -> bool:
    driver = get_driver()
    if not driver:
        return False

    try:
        with driver.session() as session:
            # Create repo node
            session.run(
                "MERGE (r:Repository {id: $id}) SET r.name = $id",
                id=repo_id,
            )

            for pf in parsed_files:
                # Create file node
                session.run(
                    """
                    MERGE (f:File {path: $path, repo: $repo})
                    SET f.language = $language,
                        f.functions = $functions,
                        f.classes = $classes
                    """,
                    path=pf.file_path,
                    repo=repo_id,
                    language=pf.language,
                    functions=pf.functions,
                    classes=pf.classes,
                )

                # Link to repo
                session.run(
                    """
                    MATCH (r:Repository {id: $repo}), (f:File {path: $path, repo: $repo})
                    MERGE (r)-[:CONTAINS]->(f)
                    """,
                    repo=repo_id,
                    path=pf.file_path,
                )

                # Create function nodes and link to file
                for func_name in pf.functions:
                    session.run(
                        """
                        MERGE (fn:Function {name: $name, file: $file, repo: $repo})
                        WITH fn
                        MATCH (f:File {path: $file, repo: $repo})
                        MERGE (f)-[:DEFINES]->(fn)
                        """,
                        name=func_name,
                        file=pf.file_path,
                        repo=repo_id,
                    )

                # Create class nodes
                for class_name in pf.classes:
                    session.run(
                        """
                        MERGE (c:Class {name: $name, file: $file, repo: $repo})
                        WITH c
                        MATCH (f:File {path: $file, repo: $repo})
                        MERGE (f)-[:DEFINES]->(c)
                        """,
                        name=class_name,
                        file=pf.file_path,
                        repo=repo_id,
                    )

                # Create import relationships
                for imp in pf.imports:
                    # Extract module name from import statement
                    parts = imp.strip().split()
                    if len(parts) >= 2:
                        module = parts[1].split(".")[0].strip("'\"")
                        session.run(
                            """
                            MATCH (f:File {path: $path, repo: $repo})
                            MERGE (m:Module {name: $module, repo: $repo})
                            MERGE (f)-[:IMPORTS]->(m)
                            """,
                            path=pf.file_path,
                            repo=repo_id,
                            module=module,
                        )

        logger.info(f"Stored graph relationships for repo {repo_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to store graph relationships: {e}")
        return False


def get_file_dependencies(repo_id: str, file_path: str) -> Dict:
    driver = get_driver()
    if not driver:
        return {"imports": [], "imported_by": [], "functions": [], "classes": []}

    try:
        with driver.session() as session:
            imports = session.run(
                """
                MATCH (f:File {path: $path, repo: $repo})-[:IMPORTS]->(m:Module)
                RETURN m.name as module
                """,
                path=file_path,
                repo=repo_id,
            ).data()

            imported_by = session.run(
                """
                MATCH (other:File {repo: $repo})-[:IMPORTS]->(m:Module)
                WHERE m.name CONTAINS $stem
                RETURN other.path as path
                LIMIT 10
                """,
                repo=repo_id,
                stem=file_path.split("/")[-1].replace(".py", "").replace(".ts", ""),
            ).data()

            functions = session.run(
                """
                MATCH (f:File {path: $path, repo: $repo})-[:DEFINES]->(fn:Function)
                RETURN fn.name as name
                """,
                path=file_path,
                repo=repo_id,
            ).data()

            classes = session.run(
                """
                MATCH (f:File {path: $path, repo: $repo})-[:DEFINES]->(c:Class)
                RETURN c.name as name
                """,
                path=file_path,
                repo=repo_id,
            ).data()

        return {
            "imports": [r["module"] for r in imports],
            "imported_by": [r["path"] for r in imported_by],
            "functions": [r["name"] for r in functions],
            "classes": [r["name"] for r in classes],
        }
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        return {"imports": [], "imported_by": [], "functions": [], "classes": []}


def get_dependency_graph(repo_id: str, limit: int = 100) -> Dict:
    """Return nodes and edges for frontend graph visualization."""
    driver = get_driver()
    if not driver:
        return {"nodes": [], "edges": []}

    try:
        with driver.session() as session:
            files = session.run(
                """
                MATCH (f:File {repo: $repo})
                RETURN f.path as path, f.language as language
                LIMIT $limit
                """,
                repo=repo_id,
                limit=limit,
            ).data()

            relationships = session.run(
                """
                MATCH (f:File {repo: $repo})-[r:IMPORTS]->(m:Module)
                WHERE EXISTS { MATCH (f2:File {repo: $repo}) WHERE f2.path CONTAINS m.name }
                RETURN f.path as source, m.name as target, type(r) as rel
                LIMIT $limit
                """,
                repo=repo_id,
                limit=limit,
            ).data()

        nodes = [
            {"id": f["path"], "label": f["path"].split("/")[-1],
             "type": "file", "language": f.get("language", "")}
            for f in files
        ]
        edges = [
            {"source": r["source"], "target": r["target"], "relationship": r["rel"]}
            for r in relationships
        ]
        return {"nodes": nodes, "edges": edges}

    except Exception as e:
        logger.error(f"Dependency graph query failed: {e}")
        return {"nodes": [], "edges": []}


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
