@echo off
start http://127.0.0.1:8000/
"C:\Users\fatim\AppData\Local\Programs\Python\Python312-Real\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
