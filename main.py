import flet as ft
import sys
import traceback

def main(page: ft.Page):
    page.title = "诊断工具"
    page.scroll = ft.ScrollMode.AUTO
    
    def log(msg, color="black", size=16):
        page.add(ft.Text(msg, color=color, size=size, selectable=True))
        page.update()

    log("✅ Flet引擎启动成功！看到这个画面，说明APP打包完全没问题！", color="green", size=20)
    log("-" * 30)

    try:
        import os
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        zip_path = os.path.join(base_dir, "data.zip")
        
        log(f"当前工作目录: {base_dir}")
        
        if os.path.exists(zip_path):
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            log(f"🎉 找到 data.zip！大小为: {size_mb:.2f} MB", color="blue")
            if size_mb > 50:
                log("⚠️ 警告：压缩包极大！这是导致白屏的高危因素。", color="orange")
        else:
            log("❌ 没有找到 data.zip 文件！", color="red")
        
        log("-" * 30)
        log("当前目录下的文件列表：")
        for f in os.listdir(base_dir):
            log(f" 📄 {f}")

    except Exception as e:
        log(f"发生异常:\n{traceback.format_exc()}", color="red")

ft.app(target=main)
