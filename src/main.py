import flet as ft
import asyncio
from app_state import AppState
from ws_client import WSClient
from ui_components import create_card, create_status_badge, create_button, BG_CARD_COLOR, PRIMARY_COLOR

async def main(page: ft.Page):
    page.title = "Smart Home"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.window.width = 400
    page.window.height = 800

    # Инициализация состояния и WebSocket-клиента
    state = AppState()
    ws_client = WSClient(state, hub_ip="192.168.4.1")

    # 1. Секция: Главная
    view_main = ft.Column([
        create_status_badge("HUB: Ожидание..."),
        ft.Container(height=10),
        create_card("Реле", "Ожидание...", ft.Icons.WIFI),
        create_card("Датчик температуры", "Ожидание...", ft.Icons.WIFI)
    ])

    # 2. Секция: Реле
    view_relay = ft.Column([
        ft.Row([
            create_status_badge("Реле: Ожидание..."),
            create_button("Обновить", ft.Icons.REFRESH)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(height=10),
        create_card(
            "Реле", 
            "Ожидание...", 
            None,
            ft.Switch(value=False, disabled=True, on_change=lambda e: asyncio.create_task(ws_client.toggle_relay(e.control.value)), active_color=PRIMARY_COLOR)
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("История активности Реле", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.Text("Время Статус", weight=ft.FontWeight.W_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_CARD_COLOR,
            border_radius=10,
            padding=20,
            margin=ft.margin.symmetric(vertical=10),
            border=ft.border.all(1, ft.Colors.BLACK12),
            expand=True
        )
    ])

    # 3. Секция: Температура
    view_temp = ft.Column([
         ft.Row([
            create_status_badge("Датчик температуры: Ожидание...")
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(height=10),
        create_card(
            "Датчик температуры", 
            "Ожидание...", 
            None,
            create_button("Обновить", ft.Icons.REFRESH)
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("График температуры и влажности", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_CARD_COLOR,
            border_radius=10,
            padding=20,
            border=ft.border.all(1, ft.Colors.BLACK12),
            expand=True
        )
    ])

    views = [view_main, view_relay, view_temp]
    
    current_view_container = ft.Container(content=views[0], expand=True, padding=20)
    
    def update_all_views():
        # 1. Главная
        view_main.controls[0] = create_status_badge(f"HUB: {'Подключен' if state.hub_connected else 'Отключен'}")
        view_main.controls[2] = create_card("Реле", f"Положения: {'включен' if state.relay_state else 'выключен'}", ft.Icons.WIFI)
        view_main.controls[3] = create_card("Датчик температуры", f"Температура: {state.temp_val} C\nВлажность: {state.hum_val} %", ft.Icons.WIFI)
        
        # 2. Реле
        view_relay.controls[0].controls[0] = create_status_badge(f"Реле: {'Подключен' if state.relay_connected else 'Отключен'}")
        view_relay.controls[2] = create_card(
            "Реле", 
            f"Положения: {'включен' if state.relay_state else 'выключен'}", 
            None,
            ft.Switch(value=state.relay_state, disabled=not state.relay_connected, on_change=lambda e: asyncio.create_task(ws_client.toggle_relay(e.control.value)), active_color=PRIMARY_COLOR)
        )
        
        # 3. Температура
        view_temp.controls[0].controls[0] = create_status_badge(f"Датчик температуры: {'Подключен' if state.sensor_connected else 'Отключен'}")
        view_temp.controls[2] = create_card(
            "Датчик температуры", 
            f"Температура: {state.temp_val} C\nВлажность: {state.hum_val} %", 
            None,
            create_button("Обновить", ft.Icons.REFRESH)
        )
        
        page.update()

    # Привязываем обновление UI к изменению состояния
    state.on_state_change = update_all_views

    def on_nav_change(e):
        idx = e.control.selected_index
        current_view_container.content = views[idx]
        page.update()

    # Нижняя панель навигации (NavigationBar)
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Главная"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR_BORDER, selected_icon=ft.Icons.STAR, label="Реле"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR_BORDER, selected_icon=ft.Icons.STAR, label="Температура"),
        ],
        on_change=on_nav_change,
        selected_index=0,
        bgcolor=BG_CARD_COLOR,
    )

    page.add(current_view_container)
    
    # Первое обновление для установки начальных значений
    update_all_views()
    
    # Запускаем фоновую задачу подключения к WebSocket
    asyncio.create_task(ws_client.connect())

ft.run(main)
