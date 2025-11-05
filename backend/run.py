"""
DMS Simulator runner
"""
import asyncio
import uvicorn
from config import settings


def main():
    """Main entry point"""
    print(f"""
    ╔═══════════════════════════════════════════════════╗
    ║  Drone Management System (DMS) Simulator          ║
    ║  Version: {settings.APP_VERSION}                             ║
    ╚═══════════════════════════════════════════════════╝

    API Server: http://{settings.API_HOST}:{settings.API_PORT}
    API Docs:   http://{settings.API_HOST}:{settings.API_PORT}/docs
    WebSocket:  ws://{settings.API_HOST}:{settings.API_PORT}/ws

    Press Ctrl+C to stop
    """)

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
