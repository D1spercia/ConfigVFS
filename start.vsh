# --- СТАРТОВЫЙ СКРИПТ VFS-SHELL (stage5_start.vsh) ---
# Запуск: python main.py -v vfs_max.csv -s stage5_start.vsh

# 1. ПОДГОТОВКА СРЕДЫ
cd /home/user
ls 
# Ожидаем: documents photos

# 2. ТЕСТИРОВАНИЕ КОМАНДЫ TOUCH (Создание файлов)

# 2.1 Создание нового файла в текущей директории
touch new_file_1.txt
ls
# Ожидаем: documents photos new_file_1.txt

# 2.2 Создание файла в поддиректории (относительный путь)
touch documents/doc_a.txt
tree documents
# Ожидаем: documents/
#          ├── doc_a.txt
#          └── report.txt

# 2.3 Создание файла в другой ветке (абсолютный путь)
touch /etc/new_config.cfg
cd /etc
ls
# Ожидаем: config new_config.cfg

# 2.4 Использование touch на существующем файле (ничего не происходит, но нет ошибки)
touch /etc/config/service.conf
ls /etc/config
# Ожидаем: service.conf

# 2.5 Использование touch с путем, содержащим . и ..
touch ../home/user/temp_file.tmp
ls /home/user
# Ожидаем: documents photos new_file_1.txt temp_file.tmp

# 3. ТЕСТИРОВАНИЕ TOUCH (Обработка ошибок)
cd /home/user

# 3.1 Ошибка: Отсутствие аргументов
touch

# 3.2 Ошибка: Создание файла, если родительская директория не существует
touch /home/non_existent_dir/file.txt

# 3.3 Ошибка: Попытка создать файл с именем существующей директории
touch documents

# 3.4 Ошибка: Попытка создать файл внутри файла
touch documents/report.txt/file_inside_file.txt

# 4. Тест времени
date

# 5. ФИНАЛЬНАЯ ПРОВЕРКА СОСТОЯНИЯ VFS
cd /
tree

# 6. ПРОВЕРКА HISTORY
history

# 7. ВЫХОД
exit