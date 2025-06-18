"""
File operation API interfaces
"""
from fastapi import APIRouter
from fastapi.params import Form

from app.schemas.file import FileReadRequest, FileWriteRequest, FileReplaceRequest, FileSearchRequest, FileFindRequest, \
    FileDownloadRequest
from app.schemas.response import Response
from app.services.file import file_service

router = APIRouter()


@router.post("/read", response_model=Response)
async def read_file(request: FileReadRequest):
    """
    Read file content
    """
    result = await file_service.read_file(
        file=request.file,
        start_line=request.start_line,
        end_line=request.end_line,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message="File read successfully",
        data=result.model_dump()
    )


@router.post("/write", response_model=Response)
async def write_file(request: FileWriteRequest):
    """
    Write file content
    """
    result = await file_service.write_file(
        file=request.file,
        content=request.content,
        append=request.append,
        leading_newline=request.leading_newline,
        trailing_newline=request.trailing_newline,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message="File written successfully",
        data=result.model_dump()
    )


@router.post("/replace", response_model=Response)
async def replace_in_file(request: FileReplaceRequest):
    """
    Replace string in file
    """
    result = await file_service.str_replace(
        file=request.file,
        old_str=request.old_str,
        new_str=request.new_str,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message=f"Replacement completed, replaced {result.replaced_count} occurrences",
        data=result.model_dump()
    )


@router.post("/search", response_model=Response)
async def search_in_file(request: FileSearchRequest):
    """
    Search in file content
    """
    result = await file_service.find_in_content(
        file=request.file,
        regex=request.regex,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.matches)} matches",
        data=result.model_dump()
    )


@router.post("/find", response_model=Response)
async def find_files(request: FileFindRequest):
    """
    Find files by name pattern
    """
    result = await file_service.find_by_name(
        path=request.path,
        glob_pattern=request.glob
    )

    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.files)} files",
        data=result.model_dump()
    )


from fastapi import File, UploadFile


@router.post("/upload", response_model=Response)
async def upload_file(
        file: UploadFile = File(...),
        target_dir: str = Form(...),
        sudo: bool = Form(False)
):
    """
    上传文件到指定目录，保持原始文件名
    """
    result = await file_service.upload_file(
        target_dir=target_dir,
        file=file,
        sudo=sudo
    )

    return Response(
        success=True,
        message="File uploaded successfully",
        data=result.model_dump()
    )


@router.post("/download", response_model=Response)
async def download_file(request: FileDownloadRequest):
    """
    从沙箱下载文件
    """
    try:
        result = await file_service.download_file(
            sandbox_path=request.sandbox_path,
            sudo=request.sudo
        )
        
        return Response(
            success=True,
            message="File downloaded successfully",
            data=result.model_dump()
        )
    except Exception as e:
        return Response(
            success=False,
            message=str(e),
            data=None
        )
