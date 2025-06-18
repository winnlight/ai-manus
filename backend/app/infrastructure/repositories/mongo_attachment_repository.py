import logging
from typing import Optional, List

from app.infrastructure.models.documents import AttachmentDocument

logger = logging.getLogger(__name__)


class AttachmentRepository:
    async def save(self, attachment: AttachmentDocument) -> AttachmentDocument:
        await attachment.save()
        return attachment

    async def find_by_id(self, _id: str) -> Optional[AttachmentDocument]:
        return await AttachmentDocument.find_one({"_id": _id})

    async def find_by_session_id(self, session_id: str) -> List[AttachmentDocument]:
        return await AttachmentDocument.find({"session_id": session_id}).to_list()

    async def delete(self, attachment_id: str) -> bool:
        result = await AttachmentDocument.find_one({"attachment_id": attachment_id})
        if result:
            await result.delete()
            logger.info(f"删除元数据成功")
            return True
        return False
