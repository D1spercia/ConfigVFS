import os
import shlex
import argparse
import csv
import base64
from io import StringIO

class VFS:
    def __init__(self):
        self.root = {'type': 'dir', 'children': {}}
        self.current_path = [] # Путь к текущей директории

    def load_from_csv(self, csv_file_path):
        # Загружает VFS из CSV-файла
        self.root = {'type': 'dir', 'children': {}}
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    path_parts = row['path'].strip('/').split('/')
                    current_dir = self.root
                    for part in path_parts:
                        if part not in current_dir['children']:
                            current_dir['children'][part] = {'type': 'dir', 'children': {}}
                        current_dir = current_dir['children'][part]

                    #теперь current_dir это нужный нам элемент
                    if row['type'] == 'file':
                        current_dir['type'] = 'file'
                        current_dir['content'] = row['content']
                    elif row['type'] == 'dir':
                        current_dir['type'] = 'dir'

        except FileNotFoundError:
            raise Exception(f"Ошибка: csv-файл '{csv_file_path}' не найден")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке csv: {e}")
        
    def list_dir(self, path=None):
        # возвращает список содержимого директории
        if path == None:
            target_path_parts = self.current_path
        else:
            target_path_parts = self._normalize_path(path)

        
        target_dir = self._find_node(target_path_parts)
        
        if target_dir == None:
            print(f"ls: '{path}': No such file or directory")
            return None

        if target_dir and target_dir['type'] == 'dir':
            return list(target_dir['children'].keys())
        
        return [target_path_parts[-1]] if target_path_parts else None
    
    def _normalize_path(self, path_str):
        # Преобразует строку пути (относительную и абсолютную) в нормализованный список компонентов, обрабатывая '.' и '..'

        # определяем начальный путь: корень (для абсолютных) или текущий (для относительных)
        if path_str.startswith('/'):
            # абсолютный путь начинается с корня
            current_path_copy = []
        else:
            # относительный путь начинается с текущего
            current_path_copy = self.current_path[:]

        # Разбиваем путь, удаляя пустые части (для /a//b или /)
        raw_parts = [p for p in path_str.split('/') if p]

        # Обрабатываем '..' и '.'
        for part in raw_parts:
            if part == '.':
                continue # игнорируем '.'
            elif part == '..':
                # переходим на уровень вверх: удаляем последний компонент, если не в корне
                if current_path_copy:
                    current_path_copy.pop()
            else:
                current_path_copy.append(part)
        
        return current_path_copy
    
    def _find_node(self, path_parts):
        # Находит узел по нормализованному списку компонентов пути
        node = self.root
        for part in path_parts:
            if 'children' in node and part in node['children']:
                node = node['children'][part]
            else:
                return None # узел не найден
        return node

    def change_dir(self, path):
        # изменяет текущую директорию
        # - path: строка, представляющая целевой путь
        # - пустой path или path='.' сохраняет текущую директорию
        # - path='/' переводит в корень

        # проверяем случай пустого аргумента (cd)
        if not path or path == '.':
            return True #остаёмся в текущей директории
        
        # нормализуем путь
        target_path_parts = self._normalize_path(path)

        # находим целевой узел
        target_node = self._find_node(target_path_parts)

        if target_node is None:
            print(f"cd: '{path}': No such file or directory")
            return False
        
        if target_node['type'] != 'dir':
            print(f"cd: '{path}': Not a directory")
            return False

        # Обновляем текущий путь
        self.current_path = target_path_parts
        return True

def get_home_dir():
    return os.getenv('HOME') or os.getenv('USERPROFILE')

def commParser(comm):
    parts = shlex.split(comm) # умное разделение, считает всё в кавычках как один элемент, пробелами разделяет элементы
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]

    processed_args = []

    for arg in args:
        if arg == '$HOME':
            vfs_home = '/home/user'
            processed_args.append(vfs_home)
        elif arg.startswith('$'): # если начинается с $, то переменная окружения
            var_name = arg[1:]
            env_value = os.getenv(var_name)

            if env_value is not None:
                processed_args.append(env_value)
            else:
                print(f"Ошибка: переменная окружения {var_name} не найдена")
                processed_args.append(arg)
        else: # обычный аргумент
            processed_args.append(arg)
    return command, processed_args

# Выполняет команды из файла, имитируя диалог
def execute_script(script_path, commands_dict):
    print(f"\n--- Выполнение скрипта: {script_path} ---\n")
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                # удаляем лишние пробелы и символы перевода строки
                command_line = line.strip()

                if not command_line or command_line.startswith('#'):
                    continue # пропускаем пустые строки и комментарии

                # отображаем команду, как если бы её ввёл пользователь
                print(f"VFS> {command_line}")

                try:
                    command, args = commParser(command_line)

                    if command is None:
                        continue
                    elif command not in commands_dict:
                        print(f"Ошибка (строка {line_number}): Команда '{command}' не найдена")
                    elif command == 'exit':
                        commands_dict[command](args)
                        return # завершаем выполнение скрипта, если встретили exit
                    else:
                        commands_dict[command](args)
                
                except Exception as e:
                    # Ловим и обрабатываем любые ошибки парсинга/выполнения
                    print(f"Ошибка выполнения (строка {line_number}): {e}")

    except FileNotFoundError:
        print(f"Ошибка: Стартовый скрипт '{script_path}' не найден")
    print("\n--- Скрипт завершён ---\n")


#функции команд
def ls_comm(args, vfs):
    contents = vfs.list_dir(args[0] if args else None)
    if contents is not None:
        print(' '.join(contents))

def cd_comm(args, vfs):
    target_path = args[0] if args else ''
    vfs.change_dir(target_path)

def exit_comm(args):
    print("Выход из программы.")
    raise SystemExit



def main():
    parser = argparse.ArgumentParser(description="Эмулятор языка оболочки ОС (VFS Shell)")

    # путь к физическому расположение VFS
    parser.add_argument('-v', '--vfs-path', 
                        required=True, # теперь путь к CSV обязателен 
                        help='Путь к CSV-файлу с описанием VFS')
    
    parser.add_argument('-s', '--script', 
                        default=None, 
                        help='Путь к стартовому скрипту для выполнения команд')
    
    args = parser.parse_args()

    print("--- Параметры запуска ---")
    print(f"VFS Path:{args.vfs_path}")
    print(f"Start Script:{args.script}")
    print("-------------------------")

    vfs = VFS()

    try:
        vfs.load_from_csv(args.vfs_path)
    except Exception as e:
        print(e)
        return # Завершаем, если не удалось загрузить VFS

    commands = {
    'ls' : lambda a: ls_comm(a, vfs),
    'cd' : lambda a: cd_comm(a, vfs),
    'exit' : exit_comm
}

    # Логика запуска: Скрипт или REPL
    if args.script:
        execute_script(args.script, commands)
        return
    else:
        while True:
            try:
                prompt_path = '/' + '/'.join(vfs.current_path)
                user_input = input(f"VFS{prompt_path}>")
                if not user_input:
                    continue

                # обработка команд
                command, args = commParser(user_input)

                if command == None:
                    continue
                elif command not in commands:
                    print(f"комманда {command} не найдена")
                else:
                    commands[command](args)

            #обработка ошибок
            except SystemExit:
                break
            except KeyboardInterrupt:
                print("\n^C")


if __name__ == "__main__":
    main()