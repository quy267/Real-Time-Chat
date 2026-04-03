"""PresenceStatus value object — enum of user online states."""

from enum import Enum


class PresenceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    DND = "dnd"
