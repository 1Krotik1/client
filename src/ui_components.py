import flet as ft

# Цвета
BG_CARD_COLOR = "#FAEDFA"
PRIMARY_COLOR = "#5A4C91"

def create_card(title, subtitle, icon, right_content=None):
    content_items = [
        ft.Column([
            ft.Text(title, size=16, weight=ft.FontWeight.W_600),
            ft.Text(subtitle, size=14, color=ft.Colors.GREY_700),
        ], expand=True),
    ]
    
    if right_content:
        content_items.append(right_content)
    elif icon:
        content_items.append(ft.Icon(icon, size=30, color=ft.Colors.BLACK))
        
    return ft.Container(
        content=ft.Row(content_items, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=BG_CARD_COLOR,
        border_radius=10,
        padding=20,
        margin=ft.margin.symmetric(vertical=10),
        border=ft.border.all(1, ft.Colors.BLACK12)
    )

def create_status_badge(text):
    return ft.Container(
        content=ft.Text(text, size=14),
        border=ft.border.all(1, ft.Colors.BLACK26),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=15, vertical=8),
    )
    
def create_button(text, icon):
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=16, color=PRIMARY_COLOR), 
            ft.Text(text, color=PRIMARY_COLOR)
        ], alignment=ft.MainAxisAlignment.CENTER),
        border=ft.border.all(1, ft.Colors.BLACK26),
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
    )
