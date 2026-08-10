from abc import ABC, abstractmethod


class BaseParser(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_models(self, limit: int = 10) -> list[dict]:
        ...
