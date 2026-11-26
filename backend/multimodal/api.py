import time
import base64
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union
from datetime import datetime, timezone
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .models import (
    StandardExtractionResult,
    BatchExtractionResult,
    BatchProcessRequest,
    BatchFileItem,
    SingleFileProcessRequest
)
from .processor import process_file_data
from .ocr_engine import is_ocr_available, is_tesseract_available, get_active_ocr_engine_name
from .config import SUPPORTED_EXTENSIONS, BASE_DIR

logger = logging.getLogger("multimodal_processor.api")
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB limit

app = FastAPI(
    title="CERBERUS-XA Multimodal Data Processing API",
    description="Multimodal evidence extractor converting PDF, Scanned PDF, Images, Excel, and CSV into unified JSON graphs for Member 2.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS for local cross-origin connections between team members
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def content_type_routing_middleware(request: Request, call_next):
    """
    Transparently normalizes request routing between multipart file uploads and JSON payloads:
    - If /process-batch receives application/json -> routes to /process_batch
    - If /process_batch receives multipart/form-data -> routes to /process-batch
    - If /process-file receives application/json -> routes to /process_file
    - If /process_file receives multipart/form-data -> routes to /process-file
    """
    path = request.scope.get("path", "")
    ct = request.headers.get("content-type", "")

    if path == "/process-batch" and "application/json" in ct:
        request.scope["path"] = "/process_batch"
    elif path == "/process_batch" and "multipart/form-data" in ct:
        request.scope["path"] = "/process-batch"
    elif path == "/process-file" and "application/json" in ct:
        request.scope["path"] = "/process_file"
    elif path == "/process_file" and "multipart/form-data" in ct:
        request.scope["path"] = "/process-file"

    return await call_next(request)

def _resolve_file_bytes_and_name(item: Union[BatchFileItem, str]) -> Tuple[bytes, str]:
    """Resolves raw bytes and filename from a BatchFileItem model or file path string."""
    if isinstance(item, str):
        p = Path(item)
        candidates = [
            p,
            BASE_DIR / p,
            BASE_DIR / "samples" / p.name,
            Path.cwd() / p,
            Path.cwd() / "multimodal_processor" / "samples" / p.name
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                return c.read_bytes(), c.name
        raise FileNotFoundError(f"File not found on disk: '{item}'")

    elif isinstance(item, BatchFileItem):
        fname = item.filename
        p_str = item.file_path or item.path
        raw = item.content or item.data or item.base64_content

        if p_str:
            p = Path(p_str)
            candidates = [
                p,
                BASE_DIR / p,
                BASE_DIR / "samples" / p.name,
                Path.cwd() / p,
                Path.cwd() / "multimodal_processor" / "samples" / p.name
            ]
            for c in candidates:
                if c.exists() and c.is_file():
                    return c.read_bytes(), fname or c.name
            raise FileNotFoundError(f"File not found on disk: '{p_str}'")

        if raw is not None:
            try:
                decoded = base64.b64decode(raw, validate=True)
                if len(decoded) > 0:
                    return decoded, fname or "uploaded_file"
            except Exception:
                pass
            return raw.encode("utf-8"), fname or "uploaded_file.txt"

        if fname:
            sample_p = BASE_DIR / "samples" / fname
            if sample_p.exists():
                return sample_p.read_bytes(), fname
            cwd_sample_p = Path.cwd() / "multimodal_processor" / "samples" / fname
            if cwd_sample_p.exists():
                return cwd_sample_p.read_bytes(), fname
            raise FileNotFoundError(f"No content or file_path provided for '{fname}', and not found in samples.")

    raise ValueError(f"Unable to resolve file from item: {item}")

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")

@app.get("/docs/", include_in_schema=False)
def docs_slash_redirect():
    """Ensure trailing slash redirects cleanly to /docs."""
    return RedirectResponse(url="/docs")

@app.get("/redoc/", include_in_schema=False)
def redoc_slash_redirect():
    """Ensure trailing slash redirects cleanly to /redoc."""
    return RedirectResponse(url="/redoc")

@app.get("/health", summary="Check module health and OCR availability")
def health_check():
    """Returns the operational status, supported formats, and OCR engine state."""
    return {
        "status": "healthy",
        "module": "CERBERUS-XA Multimodal Data Processor",
        "version": "1.0.0",
        "supported_formats": list(SUPPORTED_EXTENSIONS.keys()),
        "ocr_engine_available": is_ocr_available(),
        "ocr_engine": get_active_ocr_engine_name(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post(
    "/process_file",
    response_model=StandardExtractionResult,
    summary="Process a single multimodal file via JSON request"
)
def process_file_json(payload: SingleFileProcessRequest):
    """
    Accepts a single file reference, path, or base64 data via JSON,
    and returns a standardized extraction result.
    """
    item = BatchFileItem(
        filename=payload.filename,
        file_path=payload.file_path,
        path=payload.path,
        content=payload.content,
        data=payload.data,
        base64_content=payload.base64_content
    )
    content_bytes, fname = _resolve_file_bytes_and_name(item)
    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File '{fname}' exceeds maximum allowed size of 100MB"
        )
    return process_file_data(content_bytes, filename=fname)

@app.post(
    "/process-file",
    response_model=StandardExtractionResult,
    summary="Upload and extract structured evidence from a single file"
)
def process_file_endpoint(file: UploadFile = File(...)):
    """
    Accepts one file (.pdf, .jpg, .jpeg, .png, .xlsx, .xls, .csv),
    extracts structured evidence claims, and returns a standardized JSON response.
    """
    filename = file.filename or "unknown_file"
    try:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{filename}' exceeds maximum allowed size of 100MB"
            )
        result = process_file_data(content, filename=filename)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing {filename}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "source": filename,
                "source_type": "unknown",
                "content": [],
                "metadata": {
                    "filename": filename,
                    "error": f"Internal processing error: {str(e)}"
                }
            }
        )
    finally:
        try:
            file.file.close()
        except Exception:
            pass

@app.post(
    "/process_batch",
    response_model=BatchExtractionResult,
    summary="Process multiple multimodal files via JSON request"
)
def process_batch_json(payload: BatchProcessRequest):
    """
    Accepts a JSON payload containing file paths or base64 file data,
    processes each file through the multimodal extraction pipeline,
    and returns a consolidated BatchExtractionResult.
    """
    items = payload.get_all_items()
    results: List[StandardExtractionResult] = []
    errors: List[dict] = []
    successful = 0
    failed = 0

    for item in items:
        fname = getattr(item, "filename", None) or (item if isinstance(item, str) else "unknown")
        try:
            content_bytes, resolved_name = _resolve_file_bytes_and_name(item)
            fname = resolved_name
            if len(content_bytes) > MAX_FILE_SIZE_BYTES:
                failed += 1
                err_msg = f"File '{fname}' exceeds maximum allowed size of 100MB"
                errors.append({"filename": fname, "error": err_msg})
                results.append(
                    StandardExtractionResult(
                        source=fname,
                        source_type="unknown",
                        content=[],
                        metadata={"filename": fname, "error": err_msg}
                    )
                )
                continue

            res = process_file_data(content_bytes, filename=fname)
            if res.metadata.get("error"):
                failed += 1
                errors.append({"filename": fname, "error": res.metadata["error"]})
            else:
                successful += 1
            results.append(res)
        except Exception as e:
            failed += 1
            err_msg = str(e)
            logger.error(f"Error processing JSON batch item {fname}: {err_msg}")
            errors.append({"filename": str(fname), "error": err_msg})
            results.append(
                StandardExtractionResult(
                    source=str(fname),
                    source_type="unknown",
                    content=[],
                    metadata={"filename": str(fname), "error": err_msg}
                )
            )

    return BatchExtractionResult(
        total_files=len(items),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors
    )

@app.post(
    "/process-batch",
    response_model=BatchExtractionResult,
    summary="Upload and process multiple multimodal files in batch"
)
def process_batch_endpoint(files: List[UploadFile] = File(...)):
    """
    Processes a batch of files concurrently or sequentially, returning a consolidated
    batch result containing each file's standardized JSON output.
    """
    results: List[StandardExtractionResult] = []
    errors: List[dict] = []
    successful = 0
    failed = 0

    for f in files:
        fname = f.filename or "unknown"
        try:
            content = f.file.read()
            if len(content) > MAX_FILE_SIZE_BYTES:
                failed += 1
                err_msg = f"File exceeds maximum size of 100MB"
                errors.append({"filename": fname, "error": err_msg})
                results.append(
                    StandardExtractionResult(
                        source=fname,
                        source_type="unknown",
                        content=[],
                        metadata={"filename": fname, "error": err_msg}
                    )
                )
                continue

            res = process_file_data(content, filename=fname)
            if res.metadata.get("error"):
                failed += 1
                errors.append({"filename": fname, "error": res.metadata["error"]})
            else:
                successful += 1
            results.append(res)
        except Exception as e:
            failed += 1
            err_msg = str(e)
            logger.error(f"Error processing batch item {fname}: {err_msg}", exc_info=True)
            errors.append({"filename": fname, "error": err_msg})
            results.append(
                StandardExtractionResult(
                    source=fname,
                    source_type="unknown",
                    content=[],
                    metadata={"filename": fname, "error": err_msg}
                )
            )
        finally:
            try:
                f.file.close()
            except Exception:
                pass

    return BatchExtractionResult(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors
    )
