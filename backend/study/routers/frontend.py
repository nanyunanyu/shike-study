from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, dist: Path) -> None:
    if (dist / 'assets').is_dir():
        app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')

    @app.get('/{path:path}')
    def frontend(path: str):
        if path == 'api' or path.startswith(('api/', 'assets/')):
            raise HTTPException(404)
        if path == 'favicon.svg' and (dist / 'favicon.svg').is_file():
            return FileResponse(dist / 'favicon.svg')
        if (dist / 'index.html').is_file():
            return FileResponse(dist / 'index.html', headers={'Cache-Control': 'no-cache'})
        return Response(
            '前端尚未构建，请先在 frontend 目录运行 npm install && npm run build。',
            media_type='text/plain',
            status_code=503,
        )
