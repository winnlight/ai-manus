import logging
from typing import Optional

import boto3
from bson import ObjectId
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.domain.external.file_storage import FileStorage
from app.infrastructure.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class StorageFactory:
    @staticmethod
    async def create_storage() -> FileStorage:
        _settings = get_settings()
        if _settings.storage_type == "mongodb":
            return MongoDBStorage()
        elif _settings.storage_type == "s3":
            return S3Storage()
        else:
            raise ValueError(f"不支持的存储类型: {_settings.storage_type}")


class MongoDBStorage(FileStorage):
    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._fs = None

    async def initialize(self):
        if self._client is None:
            mongodb = get_mongodb()
            await mongodb.initialize()
            self._client = mongodb.client
            self._fs = AsyncIOMotorGridFSBucket(self._client[self._settings.mongodb_database])

    async def upload_file(self, file: UploadFile) -> dict:
        if self._fs is None:
            await self.initialize()

        content = await file.read()
        if len(content) > self._settings.max_file_size:
            raise ValueError("文件大小超过限制")

        file_id = await self._fs.upload_from_stream(
            file.filename, content,
            metadata={"content_type": file.content_type}
        )

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "storage_type": "mongodb",
            "storage_url": str(file_id),
            "file_size": len(content),
        }

    async def download_file(self, storage_url: str) -> Optional[dict]:

        try:
            if self._fs is None:
                await self.initialize()

            file_id = ObjectId(storage_url)
            grid_out = await self._fs.open_download_stream(file_id)
            content = await grid_out.read()

            metadata = grid_out.metadata or {}
            return {
                'content': content,
                'filename': grid_out.filename,
                'content_type': metadata.get('content_type', 'application/octet-stream'),
                'file_size': len(content),
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Failed to download file from GridFS: {str(e)}")
            return None

    async def delete_file(self, storage_url: str) -> bool:
        try:
            file_id = ObjectId(storage_url)

            await self._fs.delete(file_id)
            await self._fs.chunks.delete_many({"files_id": file_id})
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False


class S3Storage(FileStorage):
    def __init__(self):
        self._s3c = boto3.client('s3', ...)
        self._settings = get_settings()

    async def upload_file(self, file: UploadFile) -> dict:
        # 检查文件大小限制
        content = await file.read()
        if len(content) > self._settings.max_file_size:
            raise ValueError("文件大小超过限制")

        # 生成S3 key
        file_key = f"attachments//{file.filename}"

        # 上传到S3
        self._s3c.put_object(
            Bucket=self._settings.bucket_name,
            Key=file_key,
            Body=content,
            ContentType=file.content_type
        )

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "storage_type": "s3",
            "storage_url": f"s3://{self._settings.bucket_name}/{file_key}",
            "file_size": len(content),
        }
