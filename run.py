"""
在线教育平台启动入口
运行：python run.py
"""
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
