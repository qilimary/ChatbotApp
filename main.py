import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("你好！如果你能看到这行字，说明打包没有任何问题！", size=25, color="red"))

ft.app(target=main)
