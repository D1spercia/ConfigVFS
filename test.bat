@echo off
chcp 65001 > nul

SET PYTHON_EXEC=python main.py

echo --- Тест 1: Запуск с выполнением стартового скрипта ---
%PYTHON_EXEC% -s ./start.vsh

echo.
echo --- Тест 2: Запуск с обоими параметрами ---
%PYTHON_EXEC% -v D:\vsf_root -s ./start.vsh

echo --- Тест 3: Запуск в интерактивном режиме с указанием VFS Path ---
%PYTHON_EXEC% --vfs-path C:\VFS\path
pause