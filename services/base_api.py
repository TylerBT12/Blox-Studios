from __future__ import annotations

from abc import ABC, abstractmethod


class BaseGameAPI(ABC):
    provider_name: str

    @abstractmethod
    async def status(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def players(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def run_action(self, action: str, params: dict) -> dict:
        raise NotImplementedError
