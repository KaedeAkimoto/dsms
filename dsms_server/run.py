import uvicorn
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主运行函数"""
    from app.config.server import server_config
    settings = server_config.settings

    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")

    # 获取实际可用的端口
    host = settings.host
    port = server_config.get_effective_port()
    
    print(f"🚀 启动服务器，监听地址: {host}:{port}")
    print(f"   调试模式: {'开启' if settings.debug else '关闭'}")
    
    uvicorn.run(
        "app.asgi:app",
        host=host,
        port=port,
        reload=settings.debug,
        reload_dirs=[app_dir],
        log_level="info" if settings.debug else "warning",
        timeout_keep_alive=10
    )


if __name__ == "__main__":
    main()
