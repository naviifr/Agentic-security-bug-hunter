import os
from pathlib import Path
from core.models import Result

import tree_sitter_c
import tree_sitter_cpp
from tree_sitter import Language, Parser

C_LANGUAGE = Language(tree_sitter_c.language())
CPP_LANGUAGE = Language(tree_sitter_cpp.language())

PARSERS = {
    ".c": Parser(C_LANGUAGE),
    ".cc": Parser(CPP_LANGUAGE),
    ".cpp": Parser(CPP_LANGUAGE),
    ".cxx": Parser(CPP_LANGUAGE),
}

SOURCE_EXTENSIONS = set(PARSERS)

#different types of function definitions
NAME_NODE_TYPES = {"identifier", "field_identifier", "destructor_name", "operator_name"}

EXCLUDED_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "build",
    "builds",
    "dist",
    "vendor",
    "third_party",
    "node_modules",
    "__pycache__",
}

#recursively adds all the functions in the stack
def _walk(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def _function_name(function):
    node = function.child_by_field_name("declarator")

    while node is not None and node.type not in NAME_NODE_TYPES:
        if node.type == "qualified_identifier":
            node = node.child_by_field_name("name")
        else:
            node = node.child_by_field_name("declarator")

    return node.text.decode("utf-8") if node is not None else None


def discover_sources(repo_root: str | Path) -> list[Path]:

    repo_root = Path(repo_root).resolve()

    if not repo_root.is_dir():
        raise NotADirectoryError(f"Invalid repository directory: {repo_root}")

    source_files = []

    for current_dir, dirs, files in os.walk(repo_root):

        #edits the same list dirs is referencing to rather than assigning a new one to it.
        dirs[:] = [
            directory for directory in dirs
            if directory.lower() not in EXCLUDED_DIRS
        ]

        for filename in files:

            file_path = Path(current_dir) / filename

            if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue

            relative_path = file_path.relative_to(repo_root)
            source_files.append(relative_path)

    return sorted(source_files)


def discover_functions(repo_root: str | Path) -> list[dict]:

    
    source_files = discover_sources(repo_root)
    discovered_functions = []

    for source_file in source_files:
        file_path = repo_root / source_file

        parser = PARSERS[source_file.suffix.lower()]
        tree = parser.parse(file_path.read_bytes())
        root = tree.root_node

        for function in _walk(root):
            if function.type != "function_definition":
                continue

            name = _function_name(function)

            if name is None:
                continue

            discovered_functions.append({
                "name": name,
                "file": source_file.as_posix(),
                "start_line": function.start_point.row + 1,
                "end_line": function.end_point.row + 1,
            })

    return discovered_functions


def discovery_initiate(Result: Result):

    try:
        discover_functions(Result.root)

    except Exception as e:
        Result.errors["discovery_module"] = str(e)
