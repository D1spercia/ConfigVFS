@echo off
chcp 65001 > nul

SET PYTHON_EXEC=python main.py
echo.
echo --- Тест 1: Загрузка сложной VFS и выполнение стартового скрипта ---
%PYTHON_EXEC% -v vfs_max.csv -s start.vsh

echo.
echo Все тесты завершены.
pause