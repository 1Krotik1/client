import flet as ft
import websockets
import asyncio
import json

async def main(page: ft.Page):
    page.title = "Smart Home"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.window.width = 400
    page.window.height = 800

    # Цвета
    bg_card_color = "#FAEDFA"
    primary_color = "#5A4C91"
    
    websocket_task = None
    ws_connection = None
    hub_ip = "192.168.4.1"
    
    # Состояния
    hub_connected = False
    relay_connected = False
    sensor_connected = False
    relay_state = False
    temp_val = "25"
    hum_val = "30"
    
    # Логика WebSocket
    async def toggle_relay(e):
        nonlocal ws_connection, relay_state
        relay_state = e.control.value
        if ws_connection and relay_connected:
            state_int = 1 if relay_state else 0
            try:
                await ws_connection.send(f"relay/set/{state_int}")
            except Exception as ex:
                print(f"Failed to send relay command: {ex}")
        update_all_views()

    async def connect_ws():
        nonlocal ws_connection, hub_connected, temp_val, hum_val, relay_state, relay_connected, sensor_connected
        uri = f"ws://{hub_ip}:81"
        try:
            async with websockets.connect(uri) as websocket:
                ws_connection = websocket
                hub_connected = True
                update_all_views()
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "sensor_data":
                            temp_val = str(data.get('temperature', temp_val))
                            hum_val = str(data.get('humidity', hum_val))
                            sensor_connected = True
                        elif data.get("type") == "relay_state":
                            relay_state = bool(data.get("state", False))
                            relay_connected = True
                        elif data.get("type") == "relay_connection":
                            relay_connected = bool(data.get("connected", False))
                        elif data.get("type") == "sensor_connection":
                            sensor_connected = bool(data.get("connected", False))
                        update_all_views()
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"WS error: {e}")
        finally:
            ws_connection = None
            hub_connected = False
            relay_connected = False
            sensor_connected = False
            update_all_views()
            
            # Попытка переподключения через 5 секунд
            await asyncio.sleep(5)
            asyncio.create_task(connect_ws())

    # --- UI Компоненты ---

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
            bgcolor=bg_card_color,
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
                ft.Icon(icon, size=16, color=primary_color), 
                ft.Text(text, color=primary_color)
            ], alignment=ft.MainAxisAlignment.CENTER),
            border=ft.border.all(1, ft.Colors.BLACK26),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=15, vertical=5),
        )

    # 1. Секция: Главная
    view_main = ft.Column([
        create_status_badge(f"HUB: {'Подключен' if hub_connected else 'Отключен'}"),
        ft.Container(height=10),
        create_card("Реле", f"Положения: {'включен' if relay_state else 'выключен'}", ft.Icons.WIFI),
        create_card("Датчик температуры", f"Температура: {temp_val} C\nВлажность: {hum_val} %", ft.Icons.WIFI)
    ])

    # 2. Секция: Реле
    view_relay = ft.Column([
        ft.Row([
            create_status_badge(f"Реле: {'Подключен' if relay_connected else 'Отключен'}"),
            create_button("Обновить", ft.Icons.REFRESH)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(height=10),
        create_card(
            "Реле", 
            f"Положения: {'включен' if relay_state else 'выключен'}", 
            None,
            ft.Switch(value=relay_state, disabled=not relay_connected, on_change=lambda e: asyncio.create_task(toggle_relay(e)), active_color=primary_color)
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("История активности Реле", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.Text("Время Статус", weight=ft.FontWeight.W_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=bg_card_color,
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
            create_status_badge(f"Датчик температуры: {'Подключен' if sensor_connected else 'Отключен'}")
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(height=10),
        create_card(
            "Датчик температуры", 
            f"Температура: {temp_val} C\nВлажность: {hum_val} %", 
            None,
            create_button("Обновить", ft.Icons.REFRESH)
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("График температуры и влажности", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=bg_card_color,
            border_radius=10,
            padding=20,
            border=ft.border.all(1, ft.Colors.BLACK12),
            expand=True
        )
    ])

    views = [view_main, view_relay, view_temp]
    
    current_view_container = ft.Container(content=views[0], expand=True, padding=20)
    
    def update_all_views():
        # Обновляем все тексты и свитчи
        # 1. Главная
        view_main.controls[0] = create_status_badge(f"HUB: {'Подключен' if hub_connected else 'Отключен'}")
        view_main.controls[2] = create_card("Реле", f"Положения: {'включен' if relay_state else 'выключен'}", ft.Icons.WIFI)
        view_main.controls[3] = create_card("Датчик температуры", f"Температура: {temp_val} C\nВлажность: {hum_val} %", ft.Icons.WIFI)
        
        # 2. Реле
        view_relay.controls[0].controls[0] = create_status_badge(f"Реле: {'Подключен' if relay_connected else 'Отключен'}")
        view_relay.controls[2] = create_card(
            "Реле", 
            f"Положения: {'включен' if relay_state else 'выключен'}", 
            None,
            ft.Switch(value=relay_state, disabled=not relay_connected, on_change=lambda e: asyncio.create_task(toggle_relay(e)), active_color=primary_color)
        )
        
        # 3. Температура
        view_temp.controls[0].controls[0] = create_status_badge(f"Датчик температуры: {'Подключен' if sensor_connected else 'Отключен'}")
        view_temp.controls[2] = create_card(
            "Датчик температуры", 
            f"Температура: {temp_val} C\nВлажность: {hum_val} %", 
            None,
            create_button("Обновить", ft.Icons.REFRESH)
        )
        
        page.update()

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
        bgcolor="#FAEDFA", # Нежно-фиолетовый цвет фона как в макете
    )

    page.add(current_view_container)
    
    # Запускаем фоновую задачу подключения к WebSocket
    asyncio.create_task(connect_ws())

ft.run(main)
