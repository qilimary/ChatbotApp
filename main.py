import flet as ft
import importlib
import time
import random
import re
from datetime import datetime
import traceback  # 新增：用于捕获详细的错误堆栈
import os

# 全局变量，用来记录导入期间的致命错误
import_error_msg = None
bot_core = None

# 尝试动态导入你的主程序
try:
    bot_core = importlib.import_module("李尔")
except Exception as e:
    bot_core = None
    # 捕获最顶层的崩溃信息
    import_error_msg = f"【动态导入失败】\n错误类型: {type(e).__name__}\n错误信息: {e}\n\n详细堆栈:\n{traceback.format_exc()}"

def main(page: ft.Page):
    page.title = "我的AI伙伴"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 【防御机制 1】如果还没进主界面程序就崩了，直接把错误画在屏幕上，拒绝白屏！
    if import_error_msg:
        page.add(
            ft.AppBar(title=ft.Text("智能助手 - 启动失败"), bgcolor=ft.colors.RED_400),
            ft.Container(
                content=ft.Column([
                    ft.Text("糟糕，程序在加载『李尔.py』时崩溃了！", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
                    ft.Divider(),
                    ft.Text("请长按下方文字复制或截图发给 AI 分析原因：", size=14, color=ft.colors.GREY_700),
                    ft.TextField(value=import_error_msg, multiline=True, read_only=True, min_lines=10, max_lines=25),
                ], scroll=ft.ScrollMode.AUTO),
                padding=20
            )
        )
        page.update()
        return

    current_sid = None
    chat_history_list = page.client_storage.get("chat_history") or []

    chat_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    user_input = ft.TextField(hint_text="输入消息...", expand=True, on_submit=lambda e: send_msg())
    send_btn = ft.IconButton(ft.icons.SEND, on_click=lambda e: send_msg())
    
    def save_history():
        nonlocal chat_history_list
        chat_history_list = chat_history_list[-5:]
        page.client_storage.set("chat_history", chat_history_list)
        update_drawer()

    def create_chat_bubble(is_user=True):
        color = ft.colors.BLUE_100 if is_user else ft.colors.GREY_200
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        
        text_control = ft.Text(spans=[], selectable=True, size=15, color=ft.colors.BLACK87)
        container = ft.Container(
            content=text_control,
            bgcolor=color,
            padding=10,
            border_radius=10,
            max_width=page.width * 0.8
        )
        return ft.Row([container], alignment=align), text_control

    def render_current_chat(messages):
        chat_column.controls.clear()
        for msg in messages:
            bot_bubble, text_control = create_chat_bubble(is_user=False)
            _typeout_text_with_effects(msg, text_control, instant=True)
            chat_column.controls.append(bot_bubble)
        page.update()

    def check_bot_status():
        if not bot_core: return
        try:
            session = bot_core.WEB_SESSION_MANAGER.get_session(current_sid)
            if session and not getattr(session.engine, "is_active", True):
                user_input.disabled = True
                send_btn.disabled = True
                user_input.hint_text = "对话已结束，请点击右上角 '+' 刷新"
                page.update()
        except Exception:
            pass

    def _typeout_text_with_effects(text, text_control, instant=False):
        current_color = ft.colors.BLACK87
        current_weight = ft.FontWeight.NORMAL
        current_decoration = ft.TextDecoration.NONE

        tokens = re.split(r'(\x1b\[.*?m)', str(text))
        
        for tok in tokens:
            if tok.startswith('\x1b['):
                if tok == '\x1b[0m' or tok == '\033[0m':
                    current_color = ft.colors.BLACK87
                    current_weight = ft.FontWeight.NORMAL
                    current_decoration = ft.TextDecoration.NONE
                elif '38;5;210' in tok or '31m' in tok:
                    current_color = ft.colors.RED_400
                elif '1m' in tok:
                    current_weight = ft.FontWeight.BOLD
                elif '4m' in tok:
                    current_decoration = ft.TextDecoration.UNDERLINE
            elif tok:
                span = ft.TextSpan("", style=ft.TextStyle(
                    color=current_color, 
                    weight=current_weight, 
                    decoration=current_decoration
                ))
                text_control.spans.append(span)
                
                for char in tok:
                    span.text += char
                    if not instant:
                        page.update()
                        time.sleep(random.uniform(0.0215, 0.033))
                        
                if instant:
                    page.update()

    def send_msg():
        if not user_input.value or user_input.disabled or not bot_core: return
        text = user_input.value.strip()
        user_input.value = ""
        user_input.disabled = True
        send_btn.disabled = True
        
        user_bubble, user_text = create_chat_bubble(is_user=True)
        user_text.spans.append(ft.TextSpan(text, style=ft.TextStyle(color=ft.colors.BLACK87)))
        chat_column.controls.append(user_bubble)
        page.update()
        
        session_data = next((item for item in chat_history_list if item["sid"] == current_sid), None)
        if session_data and session_data["topic"] == "新对话...":
            session_data["topic"] = text[:10] + "..." if len(text) > 10 else text
            save_history()

        try:
            res = bot_core.web_process_message(text, current_sid)
            replies = res.get("replies", [])
            
            for reply in replies:
                bot_bubble, text_control = create_chat_bubble(is_user=False)
                chat_column.controls.append(bot_bubble)
                page.update()
                
                _typeout_text_with_effects(reply, text_control, instant=False)
                time.sleep(0.3)
        except Exception as ex:
            err_bubble, err_text = create_chat_bubble(is_user=False)
            err_text.spans.append(ft.TextSpan(f"发送消息失败: {ex}", style=ft.TextStyle(color="red")))
            chat_column.controls.append(err_bubble)

        user_input.disabled = False
        send_btn.disabled = False
        user_input.focus()
        page.update()
        check_bot_status()

    def start_new_chat(e=None):
        if not bot_core:
            err_bubble, err_text = create_chat_bubble(is_user=False)
            err_text.spans.append(ft.TextSpan("错误：找不到李尔.py！", style=ft.TextStyle(color="red")))
            chat_column.controls.append(err_bubble)
            page.update()
            return
            
        # 【防御机制 2】捕获初始化 Session 时的路径或逻辑崩溃，直接在聊天窗内打印详情
        try:
            nonlocal current_sid
            res = bot_core.web_start_session()
            current_sid = res["session_id"]
            
            user_input.disabled = False
            send_btn.disabled = False
            user_input.hint_text = "输入消息..."
            chat_column.controls.clear()
            
            messages = bot_core.WEB_SESSION_MANAGER.get_session(current_sid).get_all_messages()
            if messages:
                bot_bubble, text_control = create_chat_bubble(is_user=False)
                chat_column.controls.append(bot_bubble)
                _typeout_text_with_effects(messages[-1], text_control, instant=False)

            now_str = datetime.now().strftime("%H:%M")
            chat_history_list.append({"sid": current_sid, "topic": "新对话...", "time": now_str})
            save_history()
            check_bot_status()
            page.update()
        except Exception as ex:
            chat_column.controls.clear()
            chat_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("【初始化会话崩溃】", size=16, weight="bold", color="red"),
                        ft.Text(f"通常由于『李尔.py』内部读取数据时找不到相对路径导致。\n\n错误原因: {ex}\n\n详细调用栈:\n{traceback.format_exc()}", color="black", selectable=True)
                    ]),
                    bgcolor=ft.colors.RED_50, padding=10, border_radius=10
                )
            )
            page.update()

    def delete_history(sid):
        nonlocal chat_history_list
        chat_history_list = [item for item in chat_history_list if item["sid"] != sid]
        save_history()

    def switch_chat(sid):
        nonlocal current_sid
        current_sid = sid
        try:
            session = bot_core.WEB_SESSION_MANAGER.get_session(sid)
            if session:
                render_current_chat(session.get_all_messages())
                user_input.disabled = False
                send_btn.disabled = False
                user_input.hint_text = "输入消息..."
            else:
                raise Exception("Session 不存在")
        except Exception:
            chat_column.controls.clear()
            bot_bubble, text_control = create_chat_bubble(is_user=False)
            text_control.spans.append(ft.TextSpan("该对话已在后台清理或加载失败", style=ft.TextStyle(color="red")))
            chat_column.controls.append(bot_bubble)
            user_input.disabled = True
            send_btn.disabled = True
            user_input.hint_text = "无法发言"
            
        page.drawer.open = False
        page.update()
        check_bot_status()

    def update_drawer():
        drawer_items = [
            ft.Container(height=50),
            ft.Text("   历史对话 (近5次)", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider()
        ]
        for item in reversed(chat_history_list):
            sid = item["sid"]
            drawer_items.append(
                ft.ListTile(
                    title=ft.Text(item["topic"]),
                    subtitle=ft.Text(item["time"]),
                    leading=ft.Icon(ft.icons.CHAT_BUBBLE_OUTLINE),
                    on_click=lambda e, s=sid: switch_chat(s),
                    on_long_press=lambda e, s=sid: delete_history(s)
                )
            )
        page.drawer.controls = drawer_items
        page.update()

    page.drawer = ft.NavigationDrawer(controls=[])
    page.appbar = ft.AppBar(
        leading=ft.IconButton(ft.icons.MENU, on_click=lambda e: setattr(page.drawer, 'open', True) or page.update()),
        title=ft.Text("我的机器人"),
        actions=[ft.IconButton(ft.icons.ADD, on_click=start_new_chat)]
    )

    page.add(chat_column, ft.Row([user_input, send_btn]))

    # 进入程序时安全初始化
    if not current_sid and bot_core:
        start_new_chat()

ft.app(target=main)
