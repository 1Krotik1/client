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

    # Инициализация состояния и WebSocket-клиента
    state = AppState()
    ws_client = WSClient(state, hub_ip="192.168.4.1")

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
                    ft.Text("Время", weight=ft.FontWeight.W_500, expand=1),
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
            create_button_with_action("Обновить", ft.Icons.REFRESH, lambda e: asyncio.create_task(ws_client.request_history()))
        )
        
        # Обновление истории реле
        relay_history_column.controls.clear()
        if not state.relay_history:
            relay_history_column.controls.append(ft.Text("Нет данных", color=ft.Colors.BLACK54))
        for item in reversed(state.relay_history): # Свежие сверху
            ts = item.get("time", 0)
            st = item.get("state", 0)
            dt_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S') if ts > 0 else "N/A"
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
                
                # Делаем X-ось от 0 до N
                for i, item in enumerate(sorted_hist):
                    points_temp.append(fch.LineChartDataPoint(i, item.get("temp", 0)))
                    points_hum.append(fch.LineChartDataPoint(i, item.get("hum", 0)))
                
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
                        bottom_axis=fch.ChartAxis(label_size=40, show_labels=False), # Скрываем X так как там просто индекс
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
