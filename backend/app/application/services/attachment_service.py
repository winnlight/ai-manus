import base64
import logging
from typing import List

from bson import ObjectId
from fastapi import UploadFile

from app.infrastructure.models.documents import AttachmentDocument
from app.infrastructure.repositories.mongo_attachment_repository import AttachmentRepository
from app.infrastructure.storage.file_storage import StorageFactory
from app.interfaces.schemas.response import AttachmentUploadResponse, AttachmentDownloadResponse

# Set up logger
logger = logging.getLogger(__name__)


class AttachmentService:
    def __init__(self, storage_factory: StorageFactory, attachment_repository: AttachmentRepository):
        self.storage_factory = storage_factory
        self.repository = attachment_repository

    async def upload_attachment(self, file: UploadFile) -> AttachmentUploadResponse:
        storage = await self.storage_factory.create_storage()
        upload_result = await storage.upload_file(file)
        return AttachmentUploadResponse(**upload_result)

    async def download_attachment(self, storage_url: str) -> AttachmentDownloadResponse:
        """下载附件
        Args:
            storage_url: GridFS 文件的 ObjectId
        """
        # 直接从 GridFS 下载文件
        storage = await self.storage_factory.create_storage()
        result = await storage.download_file(storage_url)

        return AttachmentDownloadResponse(
            storage_url=storage_url,
            filename=result['filename'],
            content_type=result['content_type'],
            content=base64.b64encode(result['content']).decode('utf-8'),
            file_size=result['file_size']
        )

    async def bind_attachment_to_session(self, session_id: str,
                                         filename: str, content_type: str, file_size: int,
                                         storage_type: str, storage_url: str) -> AttachmentDocument:
        """将附件绑定到会话（在创建会话时调用）"""
        # 创建AttachmentDocument
        attachment = AttachmentDocument(
            attachment_id=str(ObjectId()),
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            storage_type=storage_type,
            storage_url=storage_url
        )

        # 保存到数据库
        return await self.repository.save(attachment)

    async def delete_attachment(self, _id: str) -> None:
        attachment = await self.repository.find_by_id(_id)
        if not attachment:
            return

        storage = await self.storage_factory.create_storage()
        await storage.delete_file(attachment.storage_url)
        await self.repository.delete(attachment.attachment_id)

    async def get_session_attachments(self, session_id: str) -> List[AttachmentDocument]:
        return await self.repository.find_by_session_id(session_id)

    async def get_attachments_by_session(self, session_id: str) -> List[AttachmentDocument]:
        """获取会话的所有附件
        Args:
            session_id: 会话ID
        Returns:
            List[AttachmentDocument]: 附件列表
        """
        return await self.repository.find_by_session_id(session_id)
