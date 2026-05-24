from __future__ import annotations

import carb
import omni.ext
import omni.kit.menu.utils
from omni.kit.menu.utils import MenuItemDescription

from .core.agent_controller import AgentController
from .ui.chat_window import ChatWindow


class EnergyAgentExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._ext_id = ext_id
        self._controller = AgentController()
        self._chat_window: ChatWindow | None = None
        self._menu_items = [
            MenuItemDescription(name="Energy Twin Agent", onclick_fn=self._show_window),
        ]
        omni.kit.menu.utils.add_menu_items(self._menu_items, "Window")
        carb.log_info("[Energy Twin Agent] Extension loaded")

    def on_shutdown(self):
        if self._menu_items:
            omni.kit.menu.utils.remove_menu_items(self._menu_items, "Window")
            self._menu_items = []
        if self._chat_window is not None:
            self._chat_window.destroy()
            self._chat_window = None
        self._controller = None
        carb.log_info("[Energy Twin Agent] Extension shutdown")

    def _show_window(self):
        if self._chat_window is None:
            self._chat_window = ChatWindow(self._controller)
        self._chat_window.show()

