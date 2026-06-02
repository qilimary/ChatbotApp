import flet as ft
import importlib
import time
import random
import re
from datetime import datetime

# 动态导入你的主程序
try:
    bot_core = importlib.import_module("李尔")
except Exception as e:
    bot_core = None
    print(f"导入李尔.py失败: {e}")

def main(page: ft.Page):
    page.title = "我的AI伙伴"
    page.theme_mode = ft.ThemeMode.LIGHT
    
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
        """创建一个聊天气泡，返回外层容器和内部文本控件"""
        color = ft.colors.BLUE_100 if is_user else ft.colors.GREY_200
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        
        # 使用 Text 和 Spans 来支持颜色和加粗的混合显示
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
            # 历史消息直接渲染，不需要打字机
            bot_bubble, text_control = create_chat_bubble(is_user=False)
            _typeout_text_with_effects(msg, text_control, instant=True)
            chat_column.controls.append(bot_bubble)
        page.update()

    def check_bot_status():
        if not bot_core: return
        session = bot_core.WEB_SESSION_MANAGER.get_session(current_sid)
        if session and not getattr(session.engine, "is_active", True):
            user_input.disabled = True
            send_btn.disabled = True
            user_input.hint_text = "对话已结束，请点击右上角 '+' 刷新"
            page.update()

    def _typeout_text_with_effects(text, text_control, instant=False):
        """解析你的终端 ANSI 颜色，并实现打字机特效"""
        current_color = ft.colors.BLACK87
        current_weight = ft.FontWeight.NORMAL
        current_decoration = ft.TextDecoration.NONE

        # 根据终端正则分割字符串
        tokens = re.split(r'(\x1b\[.*?m)', str(text))
        
        for tok in tokens:
            if tok.startswith('\x1b['):
                # 解析你的各种特效码
                if tok == '\x1b[0m' or tok == '\033[0m':
                    current_color = ft.colors.BLACK87
                    current_weight = ft.FontWeight.NORMAL
                    current_decoration = ft.TextDecoration.NONE
                elif '38;5;210' in tok or '31m' in tok:
                    current_color = ft.colors.RED_400  # 淡红色
                elif '1m' in tok:
                    current_weight = ft.FontWeight.BOLD  # 加粗
                elif '4m' in tok:
                    current_decoration = ft.TextDecoration.UNDERLINE  # 下划线
            elif tok:
                # 这是一个文字块，创建一个带当前样式的 Span
                span = ft.TextSpan("", style=ft.TextStyle(
                    color=current_color, 
                    weight=current_weight, 
                    decoration=current_decoration
                ))
                text_control.spans.append(span)
                
                # 逐字输出 (完全还原你原先设定的延迟时间)
                for char in tok:
                    span.text += char
                    if not instant:
                        page.update()
                        # 核心还原：0.0215 到 0.033 秒的打字停顿
                        time.sleep(random.uniform(0.0215, 0.033))
                        
                if instant:
                    page.update()

    def send_msg():
        if not user_input.value or user_input.disabled or not bot_core: return
        text = user_input.value.strip()
        user_input.value = ""
        user_input.disabled = True
        send_btn.disabled = True
        
        # 1. 显示用户消息
        user_bubble, user_text = create_chat_bubble(is_user=True)
        user_text.spans.append(ft.TextSpan(text, style=ft.TextStyle(color=ft.colors.BLACK87)))
        chat_column.controls.append(user_bubble)
        page.update()
        
        # 2. 更新抽屉记录
        session_data = next((item for item in chat_history_list if item["sid"] == current_sid), None)
        if session_data and session_data["topic"] == "新对话...":
            session_data["topic"] = text[:10] + "..." if len(text) > 10 else text
            save_history()

        # 3. 核心调用你的 3 万行逻辑处理
        res = bot_core.web_process_message(text, current_sid)
        replies = res.get("replies", [])
        
        # 4. 机器人带特效与颜色的打字机回复
        for reply in replies:
            bot_bubble, text_control = create_chat_bubble(is_user=False)
            chat_column.controls.append(bot_bubble)
            page.update()
            
            _typeout_text_with_effects(reply, text_control, instant=False)
            time.sleep(0.3) # 句子之间的停顿

        # 恢复状态
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

    def delete_history(sid):
        nonlocal chat_history_list
        chat_history_list = [item for item in chat_history_list if item["sid"] != sid]
        save_history()

    def switch_chat(sid):
        nonlocal current_sid
        current_sid = sid
        session = bot_core.WEB_SESSION_MANAGER.get_session(sid)
        if session:
            render_current_chat(session.get_all_messages())
            user_input.disabled = False
            send_btn.disabled = False
            user_input.hint_text = "输入消息..."
        else:
            chat_column.controls.clear()
            bot_bubble, text_control = create_chat_bubble(is_user=False)
            text_control.spans.append(ft.TextSpan("该对话已在后台清理", style=ft.TextStyle(color="red")))
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

    if not current_sid and bot_core:
        start_new_chat()

ft.app(target=main)
