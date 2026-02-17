@echo off
echo ========================================
echo   Instalando Oraculo
echo ========================================
echo.

echo [1/2] Instalando dependencias Python...
cd /d "%~dp0backend"
pip install -r requirements.txt

echo.
echo [2/2] Instalando dependencias Node.js...
cd /d "%~dp0frontend"
npm install

echo.
echo ========================================
echo   Instalacao concluida!
echo ========================================
echo.
echo Para iniciar:
echo   1. Execute 'iniciar-backend.bat'
echo   2. Execute 'iniciar-frontend.bat'
echo   3. Abra http://localhost:3000
echo.
pause
