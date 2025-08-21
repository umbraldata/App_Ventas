import webview
from app import app

if __name__ == '__main__':
    webview.create_window('Sistema de Ventas', app, width=1200, height=800)
    webview.start()
    app.run(host='0.0.0.0', port=5000)  # 👈 Permite que otros dispositivos accedan
