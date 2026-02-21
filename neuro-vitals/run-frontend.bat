@echo off
echo ====================================
echo  Starting Neuro-Vitals Frontend
echo ====================================
echo.
echo Opening frontend in browser...
echo.

cd frontend-app
start http://localhost:3000
python -m http.server 3000

