"""
Submission Packager for CERBERUX-XA.

Creates a clean, submission-ready ZIP archive:
- Excludes: .venv/, __pycache__/, .pytest_cache/, *.pyc, *.zip, output artifacts
- Preserves full source tree, configs, data, tests, documentation
- Prints final archive size and contents summary
"""

import os
import sys
import zipfile
from pathlib import Path

# Folders and file patterns to ignore
EXCLUDE_DIRS = {
    ".venv", "venv", "env", ".git", ".pytest_cache", "__pycache__",
    ".idea", ".vscode", "reports", "dist", "build", ".coverage"
}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".zip", ".tar", ".gz", ".log"}


def make_submission(output_zip: str = "cerberux_xa_submission.zip") -> Path:
    project_root = Path(__file__).resolve().parent.parent
    zip_path = project_root / output_zip

    print(f"📦 Packaging CERBERUX-XA from: {project_root}")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(project_root):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            rel_root = Path(root).relative_to(project_root)

            for file in files:
                file_p = Path(root) / file
                if file_p.suffix.lower() in EXCLUDE_EXTS:
                    continue
                if file == output_zip or file.endswith(".zip"):
                    continue

                arcname = str(rel_root / file)
                zf.write(file_p, arcname=arcname)
                file_count += 1
                total_uncompressed_bytes += file_p.stat().st_size

    zip_size_bytes = zip_path.stat().st_size
    zip_size_kb = zip_size_bytes / 1024.0
    zip_size_mb = zip_size_bytes / (1024.0 * 1024.0)

    print(f"\n✅ Submission package created successfully:")
    print(f"   Archive Path: {zip_path.resolve()}")
    print(f"   Files included: {file_count}")
    print(f"   Uncompressed size: {total_uncompressed_bytes / 1024.0:.1f} KB")
    print(f"   Final Archive Size: {zip_size_kb:.1f} KB ({zip_size_mb:.2f} MB)")
    return zip_path


if __name__ == "__main__":
    make_submission()
