"""
File Operation Service Implementation - Async Version
"""
import os
import re
import glob
import asyncio
from typing import Optional

from fastapi import UploadFile

from app.core.config import Settings
from app.models.file import (
    FileReadResult, FileWriteResult, FileReplaceResult,
    FileSearchResult, FileFindResult, FileUploadResult, FileDownloadResult
)
from app.core.exceptions import AppException, ResourceNotFoundException, BadRequestException


class FileService:
    """File Operation Service"""

    async def read_file(self, file: str, start_line: Optional[int] = None,
                        end_line: Optional[int] = None, sudo: bool = False) -> FileReadResult:
        """
        Asynchronously read file content
        
        Args:
            file: Absolute file path
            start_line: Starting line (0-based)
            end_line: Ending line (not included)
            sudo: Whether to use sudo privileges
        """
        # Check if file exists
        if not os.path.exists(file) and not sudo:
            raise ResourceNotFoundException(f"File does not exist: {file}")

        try:
            content = ""

            # Read with sudo
            if sudo:
                command = f"sudo cat '{file}'"
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to read file: {stderr.decode()}")

                content = stdout.decode('utf-8')
            else:
                # Asynchronously read file
                def read_file_async():
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            return f.read()
                    except Exception as e:
                        raise AppException(message=f"Failed to read file: {str(e)}")

                # Execute IO operation in thread pool
                content = await asyncio.to_thread(read_file_async)

            # Process line range
            if start_line is not None or end_line is not None:
                lines = content.splitlines()
                start = start_line if start_line is not None else 0
                end = end_line if end_line is not None else len(lines)
                content = '\n'.join(lines[start:end])

            return FileReadResult(
                content=content,
                file=file
            )
        except Exception as e:
            if isinstance(e, BadRequestException) or isinstance(e, ResourceNotFoundException):
                raise e
            raise AppException(message=f"Failed to read file: {str(e)}")

    async def write_file(self, file: str, content: str, append: bool = False,
                         leading_newline: bool = False, trailing_newline: bool = False,
                         sudo: bool = False) -> FileWriteResult:
        """
        Asynchronously write file content
        
        Args:
            file: Absolute file path
            content: Content to write
            append: Whether to append mode
            leading_newline: Whether to add a leading newline
            trailing_newline: Whether to add a trailing newline
            sudo: Whether to use sudo privileges
        """
        try:
            # Prepare content
            if leading_newline:
                content = '\n' + content
            if trailing_newline:
                content = content + '\n'

            bytes_written = 0

            # Write with sudo
            if sudo:
                mode = '>>' if append else '>'
                # Create temporary file
                temp_file = f"/tmp/file_write_{os.getpid()}.tmp"

                # Asynchronously write to temporary file
                def write_temp_file():
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return len(content.encode('utf-8'))

                bytes_written = await asyncio.to_thread(write_temp_file)

                # Use sudo to write temporary file content to target file
                command = f"sudo bash -c \"cat {temp_file} {mode} '{file}'\""
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to write file: {stderr.decode()}")

                # Clean up temporary file
                os.unlink(temp_file)
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file), exist_ok=True)

                # Asynchronously write file
                def write_file_async():
                    mode = 'a' if append else 'w'
                    with open(file, mode, encoding='utf-8') as f:
                        return f.write(content)

                bytes_written = await asyncio.to_thread(write_file_async)

            return FileWriteResult(
                file=file,
                bytes_written=bytes_written
            )
        except Exception as e:
            if isinstance(e, BadRequestException):
                raise e
            raise AppException(message=f"Failed to write file: {str(e)}")

    async def str_replace(self, file: str, old_str: str, new_str: str,
                          sudo: bool = False) -> FileReplaceResult:
        """
        Asynchronously replace string in file
        
        Args:
            file: Absolute file path
            old_str: Original string to be replaced
            new_str: New replacement string
            sudo: Whether to use sudo privileges
        """
        # First read file content
        file_result = await self.read_file(file, sudo=sudo)
        content = file_result.content

        # Calculate replacement count
        replaced_count = content.count(old_str)
        if replaced_count == 0:
            return FileReplaceResult(
                file=file,
                replaced_count=0
            )

        # Perform replacement
        new_content = content.replace(old_str, new_str)

        # Write back to file
        await self.write_file(file, new_content, sudo=sudo)

        return FileReplaceResult(
            file=file,
            replaced_count=replaced_count
        )

    async def find_in_content(self, file: str, regex: str,
                              sudo: bool = False) -> FileSearchResult:
        """
        Asynchronously search in file content
        
        Args:
            file: Absolute file path
            regex: Regular expression pattern
            sudo: Whether to use sudo privileges
        """
        # Read file
        file_result = await self.read_file(file, sudo=sudo)
        content = file_result.content

        # Process line by line
        lines = content.splitlines()
        matches = []
        line_numbers = []

        # Compile regular expression
        try:
            pattern = re.compile(regex)
        except Exception as e:
            raise BadRequestException(f"Invalid regular expression: {str(e)}")

        # Find matches (use async processing for possibly large files)
        def process_lines():
            nonlocal matches, line_numbers
            for i, line in enumerate(lines):
                if pattern.search(line):
                    matches.append(line)
                    line_numbers.append(i)

        await asyncio.to_thread(process_lines)

        return FileSearchResult(
            file=file,
            matches=matches,
            line_numbers=line_numbers
        )

    async def find_by_name(self, path: str, glob_pattern: str) -> FileFindResult:
        """
        Asynchronously find files by name pattern
        
        Args:
            path: Directory path to search
            glob_pattern: File name pattern (glob syntax)
        """
        # Check if path exists
        if not os.path.exists(path):
            raise ResourceNotFoundException(f"Directory does not exist: {path}")

        # Asynchronously find files
        def glob_async():
            search_pattern = os.path.join(path, glob_pattern)
            return glob.glob(search_pattern, recursive=True)

        files = await asyncio.to_thread(glob_async)

        return FileFindResult(
            path=path,
            files=files
        )

    async def upload_file(self, target_dir: str, file: UploadFile, sudo: bool = False) -> FileUploadResult:
        try:
            # 获取文件大小
            file_size = 0
            content = await file.read()
            file_size = len(content)
            print(file_size)
            if file_size > 200 * 1024 * 1024:
                raise BadRequestException(
                    f"File size {file_size / (1024 * 1024)}MB exceeds limit of {self._settings.max_upload_size / (1024 * 1024)}MB"
                )

            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)

            # 构建完整的文件路径
            file_path = os.path.join(target_dir, file.filename)

            # 使用sudo写入
            if sudo:
                temp_file = f"/tmp/file_upload_{os.getpid()}.tmp"

                def write_temp_file():
                    with open(temp_file, 'wb') as f:
                        f.write(content)
                    return len(content)

                bytes_written = await asyncio.to_thread(write_temp_file)

                command = f"sudo mv {temp_file} '{file_path}'"
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to upload file: {stderr.decode()}")

                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            else:
                def write_file_async():
                    with open(file_path, 'wb') as f:
                        return f.write(content)

                bytes_written = await asyncio.to_thread(write_file_async)

            return FileUploadResult(
                file=file_path,
                bytes_written=bytes_written,
                status="success"
            )
        except Exception as e:
            if isinstance(e, BadRequestException):
                raise e
            raise AppException(message=f"Failed to upload file: {str(e)}")

    async def download_file(self, sandbox_path: str, sudo: bool = False) -> FileDownloadResult:
        """
        从沙箱下载文件

        Args:
            sandbox_path: 沙箱中的源文件路径
            sudo: 是否使用sudo权限
        """
        try:
            # 检查沙箱中的文件是否存在
            if not os.path.exists(sandbox_path) and not sudo:
                raise ResourceNotFoundException(f"File does not exist in sandbox: {sandbox_path}")

            # 获取文件名
            filename = os.path.basename(sandbox_path)

            # 使用sudo读取
            if sudo:
                command = f"sudo cat '{sandbox_path}'"
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise BadRequestException(f"Failed to read file from sandbox: {stderr.decode()}")

                content = stdout
            else:
                # 直接读取文件
                def read_file_async():
                    with open(sandbox_path, 'rb') as f:
                        return f.read()

                content = await asyncio.to_thread(read_file_async)

            return FileDownloadResult(
                filename=filename,
                content=content,
                status="success"
            )
        except Exception as e:
            if isinstance(e, (BadRequestException, ResourceNotFoundException)):
                raise e
            raise AppException(message=f"Failed to download file: {str(e)}")


# Service instance
file_service = FileService()
