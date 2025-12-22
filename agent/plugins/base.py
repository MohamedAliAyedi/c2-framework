from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The command name this plugin handles (e.g. 'shell')"""
        pass

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execution logic for the plugin"""
        pass
