"""ParseMentionsUseCase — extract @username references and create Mention records."""

import re
import uuid
from uuid import UUID

from src.domain.entities.mention import Mention
from src.domain.repositories.mention_repository import MentionRepository
from src.domain.repositories.user_repository import UserRepository

_MENTION_PATTERN = re.compile(r"@(\w+)")


class ParseMentionsUseCase:
    def __init__(
        self,
        mention_repo: MentionRepository,
        user_repo: UserRepository,
    ) -> None:
        self._mention_repo = mention_repo
        self._user_repo = user_repo

    async def execute(self, content: str, message_id: str) -> list[Mention]:
        """Parse @username patterns; create Mention records for valid users only."""
        msg_uuid = UUID(message_id)
        usernames = _MENTION_PATTERN.findall(content)
        if not usernames:
            return []

        seen: set[str] = set()
        mentions: list[Mention] = []
        for username in usernames:
            if username in seen:
                continue
            seen.add(username)
            user = await self._user_repo.get_by_username(username)
            if user is None:
                continue
            mention = Mention(
                id=uuid.uuid4(),
                message_id=msg_uuid,
                mentioned_user_id=user.id,
            )
            created = await self._mention_repo.create(mention)
            mentions.append(created)

        return mentions
