import os
from pathlib import Path

SOURCE_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx"}

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
