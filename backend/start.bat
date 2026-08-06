@echo off
cd /d D:\xxxy\WorldLens\backend
venv\Scripts\activate
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890
uvicorn main:app --reload --host 127.0.0.1 --port 8000