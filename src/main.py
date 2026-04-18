import flet as ft
import flet_charts as fch
import asyncio
from datetime import datetime
from app_state import AppState
from ws_client import WSClient
from ui_components import create_card, create_status_badge, create_button, BG_CARD_COLOR, PRIMARY_COLOR

async def main(page: ft.Page):
    page.title = "Smart Home"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.window.width = 400
    page.window.height = 800

    # Простой механизм хранения настроек в файле
    import json
    import os
    config_file = "client_config.json"
    
    def load_ip():
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    return json.load(f).get("hub_ip", "")
            except Exception:
                pass
        return ""

    def save_ip(ip):
        try:
            with open(config_file, "w") as f:
                json.dump({"hub_ip": ip}, f)
        except Exception:
            pass

    # Инициализация состояния и WebSocket-клиента
    state = AppState()
    
    # Читаем сохраненный адрес из хранилища клиента.
    # Если его там нет, используем mDNS по умолчанию.
    stored_ip = load_ip()
    initial_ip = stored_ip if (stored_ip and stored_ip.strip()) else "smarthome.local"
    
    ws_client = WSClient(state, hub_ip=initial_ip)

    def create_button_with_action(text, icon, action):
        btn = create_button(text, icon)
        btn.on_click = action
        return btn

    # 1. Секция: Главная
    view_main = ft.Column([
        create_status_badge("HUB: Ожидание..."),
        ft.Container(height=10),
        create_card("Реле", "Ожидание...", ft.Icons.WIFI),
        create_card("Датчик температуры", "Ожидание...", ft.Icons.WIFI)
    ])

    # 2. Секция: Реле
    relay_history_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
    view_relay = ft.Column([
        ft.Row([
            create_status_badge("Реле: Ожидание..."),
            create_button_with_action("Обновить", ft.Icons.REFRESH, lambda e: asyncio.create_task(ws_client.request_history()))
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
                ft.Row([
                    ft.Text("Дата и Время", weight=ft.FontWeight.W_500, expand=1),
                    ft.Text("Статус", weight=ft.FontWeight.W_500, expand=1, text_align=ft.TextAlign.RIGHT),
                ]),
                ft.Divider(height=1, color=ft.Colors.BLACK12),
                relay_history_column
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_CARD_COLOR,
            border_radius=10,
            padding=20,
            margin=ft.Margin.only(top=10, bottom=10),
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK12),
                right=ft.BorderSide(1, ft.Colors.BLACK12),
                bottom=ft.BorderSide(1, ft.Colors.BLACK12),
                left=ft.BorderSide(1, ft.Colors.BLACK12)
            ),
            expand=True
        )
    ])

    # 3. Секция: Температура
    import flet.canvas as cv
    
    # Контейнер для графика
    chart_container = ft.Container(expand=True, alignment=ft.alignment.Alignment(0, 0))
    
    view_temp = ft.Column([
         ft.Row([
            create_status_badge("Датчик температуры: Ожидание...")
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(height=10),
        create_card(
            "Датчик температуры", 
            "Ожидание...", 
            None,
            create_button_with_action("Обновить", ft.Icons.REFRESH, lambda e: asyncio.create_task(ws_client.request_history()))
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("График температуры и влажности", weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                chart_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_CARD_COLOR,
            padding=20,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.PRIMARY),
                right=ft.BorderSide(1, ft.Colors.PRIMARY),
                bottom=ft.BorderSide(1, ft.Colors.PRIMARY),
                left=ft.BorderSide(1, ft.Colors.PRIMARY)
            ),
            border_radius=5, # Как на макете, немного скруглено
            expand=True
        )
    ])

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
            create_button_with_action("Обновить", ft.Icons.REFRESH, lambda e: asyncio.create_task(ws_client.request_history()))
        )
        
        # Обновление истории реле
        relay_history_column.controls.clear()
        if not state.relay_history:
            relay_history_column.controls.append(ft.Text("Нет данных", color=ft.Colors.BLACK54))
        for item in reversed(state.relay_history): # Свежие сверху
            ts = item.get("time", 0)
            st = item.get("state", 0)
            dt_str = datetime.fromtimestamp(ts).strftime('%d.%m.%Y %H:%M:%S') if ts > 0 else "N/A"
            status_str = "Включено" if st == 1 else "Выключено"
            color = PRIMARY_COLOR if st == 1 else ft.Colors.BLACK54
            
            row = ft.Row([
                ft.Text(dt_str, expand=1, color=ft.Colors.BLACK87),
                ft.Text(status_str, expand=1, text_align=ft.TextAlign.RIGHT, color=color, weight=ft.FontWeight.W_500),
            ])
            relay_history_column.controls.append(row)
            
        # Обновление графика температуры
        if state.sensor_history:
            # Для простоты используем LineChart (flet>=0.21.0 поддерживает LineChart)
            try:
                # Ограничиваем количество точек 
                points_temp = []
                points_hum = []
                # Сортируем по времени (старые -> новые)
                sorted_hist = sorted([h for h in state.sensor_history if h.get("time",0) > 0], key=lambda x: x.get("time",0))
                
                x_labels = []
                step = max(1, len(sorted_hist) // 5) # Показывать не более ~5-6 дат
                
                # Делаем X-ось от 0 до N
                for i, item in enumerate(sorted_hist):
                    points_temp.append(fch.LineChartDataPoint(i, item.get("temp", 0)))
                    points_hum.append(fch.LineChartDataPoint(i, item.get("hum", 0)))
                    
                    if i % step == 0 or i == len(sorted_hist) - 1:
                        dt_text = datetime.fromtimestamp(item.get("time", 0)).strftime('%d.%m\n%H:%M')
                        x_labels.append(fch.ChartAxisLabel(value=i, label=ft.Text(dt_text, size=10, text_align=ft.TextAlign.CENTER)))
                
                if points_temp:
                    chart = fch.LineChart(
                        data_series=[
                            fch.LineChartData(
                                points=points_temp,
                                stroke_width=2,
                                color=PRIMARY_COLOR,
                                curved=True
                            ),
                            fch.LineChartData(
                                points=points_hum,
                                stroke_width=2,
                                color=ft.Colors.BLUE,
                                curved=True
                            )
                        ],
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                            right=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                            bottom=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                            left=ft.BorderSide(1, ft.Colors.TRANSPARENT)
                        ),
                        horizontal_grid_lines=fch.ChartGridLines(interval=10, color=ft.Colors.BLACK12, width=1),
                        vertical_grid_lines=fch.ChartGridLines(interval=10, color=ft.Colors.BLACK12, width=1),
                        left_axis=fch.ChartAxis(label_size=40),
                        bottom_axis=fch.ChartAxis(labels=x_labels, label_size=35), # Показываем X с датой и временем
                        tooltip=fch.LineChartTooltip(bgcolor=ft.Colors.WHITE),
                        expand=True,
                        min_x=0,
                        max_x=len(points_temp)-1 if points_temp else 10,
                        min_y=0,
                        max_y=100  # Влажность до 100, температура до ~50
                    )
                    
                    chart_legend = ft.Row([
                        ft.Container(width=10, height=10, bgcolor=PRIMARY_COLOR, border_radius=5),
                        ft.Text("Темп.", size=12),
                        ft.Container(width=10, height=10, bgcolor=ft.Colors.BLUE, border_radius=5),
                        ft.Text("Влажн.", size=12)
                    ], alignment=ft.MainAxisAlignment.CENTER)
                    
                    chart_container.content = ft.Column([
                        chart_legend,
                        ft.Container(content=chart, expand=True, padding=10)
                    ], expand=True)
                else:
                    chart_container.content = ft.Text("Недостаточно данных для графика", color=ft.Colors.BLACK54)
            except Exception as e:
                print(f"Chart error: {e}")
                chart_container.content = ft.Text("Ошибка построения графика", color=ft.Colors.RED)
        else:
            chart_container.content = ft.Text("Нет данных датчика", color=ft.Colors.BLACK54)
            
        try:
            page.update()
        except AssertionError:
            print("Session already destroyed")
        except RuntimeError as e:
            if "destroyed session" not in str(e):
                print(f"Runtime UI error: {e}")
        except Exception as ex:
            print(f"Failed to update page: {ex}")

    # 4. Секция: Настройки
    settings_ip_input = ft.TextField(
        label="IP адрес или mDNS-имя хаба",
        value=initial_ip,
        border_color=PRIMARY_COLOR,
        focused_border_color=PRIMARY_COLOR,
        expand=True
    )
    
    def save_settings(e):
        new_ip = settings_ip_input.value.strip()
        if new_ip:
            save_ip(new_ip)
            ws_client.hub_ip = new_ip
            # Обрываем текущее websocket-подключение, чтобы класс WSClient автоматически
            # ушел в перезапуск с новым IP-адресом
            if ws_client.ws_connection:
                asyncio.create_task(ws_client.ws_connection.close())
                
            page.snack_bar = ft.SnackBar(ft.Text(f"Настройки сохранены: {new_ip}. Переподключение..."), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True
            page.update()

    view_settings = ft.Column([
        ft.Row([
            create_status_badge("Настройки подключения"),
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(height=10),
        ft.Container(
            content=ft.Column([
                ft.Text("Измените адрес, если mDNS в вашей Wi-Fi сети не поддерживается", size=14, color=ft.Colors.BLACK54),
                ft.Container(height=10),
                ft.Row([
                    settings_ip_input,
                ]),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton("Сохранить и переподключиться", on_click=save_settings, bgcolor=PRIMARY_COLOR, color=ft.Colors.WHITE)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]),
            bgcolor=BG_CARD_COLOR,
            border_radius=10,
            padding=20,
            margin=ft.Margin.only(top=10, bottom=10),
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK12),
                right=ft.BorderSide(1, ft.Colors.BLACK12),
                bottom=ft.BorderSide(1, ft.Colors.BLACK12),
                left=ft.BorderSide(1, ft.Colors.BLACK12)
            ),
            expand=True
        )
    ])

    views = [view_main, view_relay, view_temp, view_settings]
    
    current_view_container = ft.Container(content=views[0], expand=True, padding=20)
    
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
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Настройки"),
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
