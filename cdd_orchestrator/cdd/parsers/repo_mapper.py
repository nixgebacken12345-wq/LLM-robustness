import hashlib
from pathlib import Path
from typing import List, Optional
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from sqlalchemy.orm import Session
from cdd.state.db import FileRegistry, FunctionRegistry, SessionLocal, engine, Base

# Initialize Tree-Sitter
PY_LANGUAGE = Language(tspython.language(), "python")
parser = Parser()
parser.set_language(PY_LANGUAGE)

class RepoMapper:
    """
    Scans a filesystem directory and maps Python structures into the SQLite Registry.
    """
    def __init__(self, root_dir: str):
        self.root_path = Path(root_dir).resolve()
        if not self.root_path.exists():
            raise ValueError(f"Root directory {self.root_path} does not exist.")

    def get_file_hash(self, file_path: Path) -> str:
        """Computes SHA-256 hash of file content for change detection."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def parse_python_file(self, content: bytes):
        """Extracts function metadata using Tree-Sitter AST."""
        tree = parser.parse(content)
        query = PY_LANGUAGE.query("""
            (function_definition
                name: (identifier) @name
                parameters: (parameters) @params
                body: (block) @body) @func
        """)
        
        captures = query.captures(tree.root_node)
        functions = []
        
        # Tree-sitter captures are flattened; we group by the '@func' tag
        for node, tag in captures:
            if tag == "func":
                name_node = next((n for n, t in captures if t == "name" and n.parent == node), None)
                params_node = next((n for n, t in captures if t == "params" and n.parent == node), None)
                
                if name_node and params_node:
                    functions.append({
                        "name": content[name_node.start_byte:name_node.end_byte].decode("utf-8"),
                        "signature": content[params_node.start_byte:params_node.end_byte].decode("utf-8"),
                        "body_hash": hashlib.sha256(content[node.start_byte:node.end_byte]).hexdigest()
                    })
        return functions

    def scan(self):
        """Performs a full scan and updates the Registry."""
        session: Session = SessionLocal()
        try:
            for py_file in self.root_path.rglob("*.py"):
                if "venv" in py_file.parts or ".git" in py_file.parts:
                    continue
                
                rel_path = str(py_file.relative_to(self.root_path))
                current_hash = self.get_file_hash(py_file)
                
                # Check if file exists and hash is unchanged
                db_file = session.query(FileRegistry).filter_by(path=rel_path).first()
                if db_file and db_file.last_commit_hash == current_hash:
                    continue

                # Parse and Update
                with open(py_file, "rb") as f:
                    content = f.read()
                
                functions_data = self.parse_python_file(content)
                
                if not db_file:
                    db_file = FileRegistry(path=rel_path, last_commit_hash=current_hash)
                    session.add(db_file)
                    session.flush() # Get ID
                else:
                    db_file.last_commit_hash = current_hash
                    # Clear old functions for this file
                    session.query(FunctionRegistry).filter_by(file_id=db_file.id).delete()

                for func in functions_data:
                    new_func = FunctionRegistry(
                        file_id=db_file.id,
                        name=func["name"],
                        signature=func["signature"],
                        body_hash=func["body_hash"]
                    )
                    session.add(new_func)
                
            session.commit()
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Repository Scan Failed: {e}")
        finally:
            session.close()

# Unit Test Script
if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    mapper = RepoMapper(".")
    print("Starting Repository Mapping...")
    mapper.scan()
    print("Scan Complete.")