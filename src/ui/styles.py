"""
Predefined Flet TextStyles
"""

import flet as ft
import src.ui.theme as theme

TITLE = ft.TextStyle(size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT_COLOR)
LABEL = ft.TextStyle(size=theme.LABEL_SIZE, weight=ft.FontWeight.W_500, color=theme.TEXT_COLOR)
VALUE = ft.TextStyle(size=theme.VALUE_SIZE, weight=ft.FontWeight.NORMAL, color=theme.TEXT_COLOR)
UNIT = ft.TextStyle(size=theme.UNIT_SIZE, weight=ft.FontWeight.W_300, color=theme.TEXT_COLOR)
ERROR = ft.TextStyle(size=theme.ERROR_SIZE, weight=ft.FontWeight.NORMAL, color=theme.ERROR_COLOR)
