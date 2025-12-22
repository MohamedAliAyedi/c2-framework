import os
import sys
import importlib
import pkgutil
from typing import Dict, Any, List
try:
    from .plugins.base import BasePlugin
except ImportError:
    from plugins.base import BasePlugin

class Executor:
    _plugins: Dict[str, BasePlugin] = {}

    @classmethod
    def load_plugins(cls):
        """Dynamically load all plugins from the plugins directory"""
        cls._plugins = {}
        
        # Path to the plugins directory
        plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
        
        # Add to path so we can import
        if plugins_path not in sys.path:
            sys.path.append(plugins_path)

        # Iterate over modules in the plugins directory
        for _, name, is_pkg in pkgutil.iter_modules([plugins_path]):
            if name == "base":
                continue
            
            try:
                module = importlib.import_module(f"agent.plugins.{name}")
                # Look for classes that inherit from BasePlugin
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (isinstance(item, type) and 
                        issubclass(item, BasePlugin) and 
                        item is not BasePlugin):
                        plugin_instance = item()
                        cls._plugins[plugin_instance.name] = plugin_instance
                        print(f"[*] Loaded plugin: {plugin_instance.name}")
            except Exception as e:
                print(f"[!] Failed to load plugin {name}: {e}")

    @classmethod
    def execute(cls, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Routes the task to the appropriate plugin."""
        if not cls._plugins:
            cls.load_plugins()

        plugin = cls._plugins.get(task_type)
        if plugin:
            return plugin.execute(payload)
        else:
            return {"status": "error", "error": f"No plugin found for task type: {task_type}"}

    @staticmethod
    def _get_sysinfo():
        # This is used for initial registration, we can reuse the plugin logic
        from .plugins.sysinfo import SysinfoPlugin
        return SysinfoPlugin().execute({})
