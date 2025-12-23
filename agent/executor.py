import os
import sys
import importlib
import pkgutil
from typing import Dict, Any, List
# Ensure BasePlugin is available for subclass checking
try:
    from agent.plugins.base import BasePlugin
except ImportError:
    try:
        from plugins.base import BasePlugin
    except ImportError:
        from base import BasePlugin

class Executor:
    _plugins: Dict[str, BasePlugin] = {}

    @classmethod
    def load_plugins(cls):
        """Dynamically load all plugins from the plugins directory"""
        cls._plugins = {}
        
        # Path to the plugins directory
        if getattr(sys, 'frozen', False):
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            plugins_path = os.path.join(bundle_dir, "plugins")
        else:
            plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
        
        # Add to path so we can import
        if plugins_path not in sys.path:
            sys.path.append(plugins_path)

        # Discovery phase: Get all potential plugin names
        plugin_modules = []
        if os.path.exists(plugins_path):
            for filename in os.listdir(plugins_path):
                if filename.endswith(".py") and filename != "base.py" and not filename.startswith("__"):
                    plugin_modules.append(filename[:-3])

        for name in plugin_modules:
            try:
                module = None
                for prefix in ["plugins.", "agent.plugins.", ""]:
                    try:
                        module = importlib.import_module(f"{prefix}{name}")
                        break
                    except ImportError:
                        continue
                
                if not module:
                    continue

                # Look for classes that inherit from BasePlugin
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    # Check for type AND name pattern to handle frozen identity issues
                    if (isinstance(item, type) and item_name.endswith("Plugin") and item_name != "BasePlugin"):
                        try:
                            plugin_instance = item()
                            cls._plugins[plugin_instance.name] = plugin_instance
                            print(f"[*] Loaded plugin: {plugin_instance.name}")
                        except: continue
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
        # Optimization: use already loaded plugins if available
        if "sysinfo" in Executor._plugins:
            return Executor._plugins["sysinfo"].execute({})
            
        plugin = None
        for prefix in ["plugins.", "agent.plugins.", ""]:
            try:
                module = importlib.import_module(f"{prefix}sysinfo")
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (isinstance(item, type) and item_name == "SysinfoPlugin"):
                        plugin = item()
                        break
                if plugin: break
            except ImportError: continue
        
        if plugin:
            return plugin.execute({})
        return {"status": "error", "error": "Sysinfo plugin not found"}
