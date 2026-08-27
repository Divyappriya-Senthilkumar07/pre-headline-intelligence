from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class BaseAgent(Generic[TInput, TOutput], ABC):
    """
    Abstract base class for all Pre-Headline Intelligence agents.
    Enforces typed input/output contracts and modular testability.
    """
    agent_id: int
    agent_name: str
    description: str

    def __init__(self):
        if not hasattr(self, "agent_id") or not hasattr(self, "agent_name"):
            raise NotImplementedError("Subclasses must declare agent_id and agent_name.")

    @abstractmethod
    async def process(self, input_data: TInput) -> TOutput:
        """
        Execute agent processing logic on the typed input.
        """
        pass

    def __repr__(self) -> str:
        return f"<Agent {self.agent_id}: {self.agent_name}>"
