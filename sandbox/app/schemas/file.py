"""
File operation request models
"""
from pydantic import BaseModel, Field
from typing import Optional


class FileReadRequest(BaseModel):
    """File read request"""
    file: str = Field(..., description="Absolute file path")
    start_line: Optional[int] = Field(None, description="Start line (0-based)")
    end_line: Optional[int] = Field(None, description="End line (not inclusive)")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")


class FileWriteRequest(BaseModel):
    """File write request"""
    file: str = Field(..., description="Absolute file path")
    content: str = Field(..., description="Content to write")
    append: Optional[bool] = Field(False, description="Whether to use append mode")
    leading_newline: Optional[bool] = Field(False, description="Whether to add leading newline")
    trailing_newline: Optional[bool] = Field(False, description="Whether to add trailing newline")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")


class FileReplaceRequest(BaseModel):
    """File content replacement request"""
    file: str = Field(..., description="Absolute file path")
    old_str: str = Field(..., description="Original string to replace")
    new_str: str = Field(..., description="New string to replace with")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")


class FileSearchRequest(BaseModel):
    """File content search request"""
    file: str = Field(..., description="Absolute file path")
    regex: str = Field(..., description="Regular expression pattern")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")


class FileFindRequest(BaseModel):
    """File find request"""
    path: str = Field(..., description="Directory path to search")
    glob: str = Field(..., description="Filename pattern (glob syntax)")


class FileUploadRequest(BaseModel):
    """File upload request"""
    target_dir: str = Field(..., description="Target directory path")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")


class FileDownloadRequest(BaseModel):
    """File download request"""
    sandbox_path: str = Field(..., description="Source file path in sandbox")
    sudo: Optional[bool] = Field(False, description="Whether to use sudo privileges")