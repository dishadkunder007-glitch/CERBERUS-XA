from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator

class ContentItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claim: str = Field(..., description="Extracted claim, sentence, field name, or textual assertion")
    value: Optional[str] = Field(None, description="Extracted value, metric, or detail, never invented")
    unit: Optional[str] = Field(None, description="Measurement unit if detected, otherwise null")
    page: Optional[int] = Field(None, description="Page number (1-based) if document, otherwise null")
    sheet: Optional[str] = Field(None, description="Sheet name if spreadsheet, otherwise null")
    row: Optional[int] = Field(None, description="Row index (1-based) if tabular, otherwise null")
    column: Optional[str] = Field(None, description="Column header if tabular, otherwise null")
    confidence: Optional[float] = Field(None, description="OCR extraction confidence (0.0 to 1.0), otherwise null")

class StandardExtractionResult(BaseModel):
    source: str = Field(..., description="Source filename or identifier")
    source_type: str = Field(..., description="Type of source: 'document', 'image', or 'table'")
    content: List[ContentItem] = Field(default_factory=list, description="List of extracted standardized items")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata including format, processing stats, etc.")

class BatchExtractionResult(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: List[StandardExtractionResult]
    errors: List[Dict[str, Any]]

class BatchFileItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: Optional[str] = Field(None, description="Original filename with extension (e.g. report.pdf)")
    file_path: Optional[str] = Field(None, description="Path to file on disk (relative or absolute)")
    path: Optional[str] = Field(None, description="Alias for file_path")
    content: Optional[str] = Field(None, description="Base64-encoded file content or raw text")
    data: Optional[str] = Field(None, description="Alias for content")
    base64_content: Optional[str] = Field(None, description="Explicit base64 payload")

    @model_validator(mode="after")
    def validate_item_content(self) -> "BatchFileItem":
        effective_path = self.file_path or self.path
        effective_content = self.content or self.data or self.base64_content
        if not effective_path and not effective_content and not self.filename:
            raise ValueError("Each file item must specify at least a 'filename', 'file_path', or 'content'.")
        return self

class BatchProcessRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    files: Optional[List[Union[BatchFileItem, str]]] = Field(
        None,
        description="List of file items (with filename and base64 content or file_path) or list of file paths",
        json_schema_extra={
            "example": [
                "multimodal_processor/samples/sample_report.pdf",
                "multimodal_processor/samples/sample_inventory.csv"
            ]
        }
    )
    file_paths: Optional[List[str]] = Field(
        None,
        description="List of file paths on disk to process",
        json_schema_extra={
            "example": ["multimodal_processor/samples/sample_report.pdf"]
        }
    )
    items: Optional[List[Union[BatchFileItem, str]]] = Field(
        None,
        description="Alias for 'files'"
    )
    documents: Optional[List[Union[BatchFileItem, str]]] = Field(
        None,
        description="Alias for 'files'"
    )

    @model_validator(mode="after")
    def validate_has_files(self) -> "BatchProcessRequest":
        items = []
        for lst in [self.files, self.file_paths, self.items, self.documents]:
            if lst is not None and len(lst) > 0:
                items.extend(lst)
        if not items:
            raise ValueError(
                "At least one file item or file path must be provided in 'files', 'file_paths', or 'items'."
            )
        return self

    def get_all_items(self) -> List[Union[BatchFileItem, str]]:
        collected: List[Union[BatchFileItem, str]] = []
        for lst in [self.files, self.file_paths, self.items, self.documents]:
            if lst:
                for entry in lst:
                    if entry not in collected:
                        collected.append(entry)
        return collected

class SingleFileProcessRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: Optional[str] = Field(None, description="Original filename with extension (e.g. report.pdf)")
    file_path: Optional[str] = Field(None, description="Path to file on disk (relative or absolute)")
    path: Optional[str] = Field(None, description="Alias for file_path")
    content: Optional[str] = Field(None, description="Base64-encoded file content or raw text")
    data: Optional[str] = Field(None, description="Alias for content")
    base64_content: Optional[str] = Field(None, description="Explicit base64 payload")

    @model_validator(mode="after")
    def validate_file_source(self) -> "SingleFileProcessRequest":
        effective_path = self.file_path or self.path
        effective_content = self.content or self.data or self.base64_content
        if not effective_path and not effective_content and not self.filename:
            raise ValueError("Either 'file_path', 'content', or 'filename' must be provided.")
        return self
