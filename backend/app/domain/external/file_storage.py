from typing import Protocol, Optional
from fastapi import UploadFile

class FileStorage(Protocol):
    """存储接口协议"""

    async def upload_file(self, file: UploadFile) -> dict:
        """upload_file """  # 缩进过多

        """ Returns:  # 缩进不一致
            dict: { "storage_type": str,
                    "storage_url": str,
                    "file_size": int,
                    "filename": str,
                    "content_type": str  }
        """

    async def download_file(self, storage_url: str) -> Optional[bytes]:
        """下载文件
        Args:
            storage_url: 存储URL
        Returns:
            dict: 包含文件内容和元数据的字典
            {
                'content': bytes,  # 文件内容
                'filename': str,   # 文件名
                'content_type': str,  # 内容类型
                'file_size': int,  # 文件大小
                'metadata': dict   # 其他元数据
            }
        """
        ...

    async def delete_file(self, storage_url: str) -> bool:
        """delete_file"""
        ...