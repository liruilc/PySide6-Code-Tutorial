import flet as ft
import flet_webview as fwv  # 导入 flet-webview

def main(page: ft.Page):
    print("Setting up WebView...")
    
    wv = fwv.WebView(
        url="https://flet.dev",
        on_page_started=lambda _: print("Page started..."),
        on_page_ended=lambda _: print("Page ended..."),
        on_web_resource_error=lambda e: print(f"Page error: {e.data}"),
        expand=True,
    )

    print("Adding WebView to the page...")
    page.add(wv)
    print("WebView added.")


# 启动应用
ft.app(main)
