import flet as ft
import os
import tempfile
import threading
import traceback
import gdown  # 你在 requirements.txt 里配置了这个，APP 就能用它了

def main(page: ft.Page):
    page.title = "AI 引擎初始化"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 30

    # 这里的界面会【瞬间】显示，彻底告别白屏！
    status_text = ft.Text("正在启动 AI 引擎...", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    detail_text = ft.Text("首次打开需要下载核心数据模型\n请保持屏幕常亮并在有WiFi的环境下等待", size=14, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER)
    progress_ring = ft.ProgressRing(width=50, height=50, stroke_width=5)
    
    page.add(
        ft.Column(
            [progress_ring, status_text, detail_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

    def download_and_init():
        try:
            # 找到安卓手机内部绝对可读写、速度最快的临时目录
            write_dir = tempfile.gettempdir()
            zip_path = os.path.join(write_dir, "data.zip")
            
            # 如果文件已经存在（第二次打开APP），就跳过下载
            if not os.path.exists(zip_path):
                status_text.value = "正在从云端下载核心数据包..."
                page.update()
                
                # 开始在手机里直接下载！
                url = "https://drive.google.com/uc?id=1GudOlOQ5vIn7YKzkBl-J36U9kdXk2Avc"
                gdown.download(url, zip_path, quiet=False)
            
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            status_text.value = f"✅ 下载成功 (大小: {size_mb:.1f} MB)\n请关闭 APP 并等待我们下一步替换正式聊天代码！"
            status_text.color = ft.colors.GREEN
            progress_ring.visible = False
            detail_text.visible = False
            page.update()

        except Exception as e:
            progress_ring.visible = False
            status_text.value = "❌ 糟糕，下载失败了！"
            status_text.color = ft.colors.RED
            detail_text.value = traceback.format_exc()
            detail_text.color = ft.colors.RED
            detail_text.selectable = True
            page.update()

    # 启动后台线程执行下载，绝不卡死前端画面
    threading.Thread(target=download_and_init, daemon=True).start()

ft.app(target=main)
