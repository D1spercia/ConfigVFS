import os
import shlex
import argparse
import csv
import base64
from io import StringIO
from datetime import datetime
import sys

command_history = []

class VFS:
    def __init__(self): # конструктор класса
        self.root = {'type': 'dir', 'children': {}}
        self.current_path = [] # Путь к текущей директории

    def load_from_csv(self, csv_file_path):
        # Загружает VFS из CSV-файла
        self.root = {'type': 'dir', 'children': {}}
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';') # считывает первую строку, составляя из неё ключи
                for row in reader: # считывает последующие строки
                    path_parts = row['path'].strip('/').split('/') # разделяет путь на части
                    current_dir = self.root
                    for part in path_parts:
                        if part not in current_dir['children']:
                            current_dir['children'][part] = {'type': 'dir', 'children': {}} # создаёт в ключе children значение part
                        current_dir = current_dir['children'][part] # перемещаемся в нужную директорию(вниз по дереву)

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
        
        return [target_path_parts[-1]] if target_path_parts else None # возвращает последний элемент из списка(файл)
    
    def _normalize_path(self, path_str):
        # Преобразует строку пути (относительную и абсолютную) в нормализованный список компонентов, обрабатывая '.' и '..'

        # определяем начальный путь: корень (для абсолютных) или текущий (для относительных)
        if path_str.startswith('/'):
            # абсолютный путь начинается с корня
            current_path_copy = []
        else:
            # относительный путь начинается с текущего
            current_path_copy = self.current_path[:] # создаём копию пути (если бы было = self.current_path, то мы бы создали ссылку на список пути и, если бы взаимодействовали с current_path_copy, то это влияло бы и на self.current_path)

        # Разбиваем путь, удаляя пустые части (для /a//b или /)
        raw_parts = [p for p in path_str.split('/') if p] # фильтрация пустых элементов, полученных из списка после метода split

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
    
    def _create_node(self, path_parts, node_type, content=None):
        # создаёт новый узел (файл или директорию) по заданному нормализованному пути.
        # возвращает созданный узел или None, если родительский путь не существует или если узел с таким именем уже существует, но имеет другой тип
        
        if not path_parts:
            # нельзя создать узел в корне, кроме как саму корневую директорию, но это не нужно т.к. корень уже есть
            return None
        
        parent_parts = path_parts[:-1] # получаем новый список, который содержит все элементы, кроме последнего элемента исходного списка путём среза
        name = path_parts[-1] # берём последний элемент из исходного списка

        # 1. находим родительскую директорию
        parent_node = self._find_node(parent_parts)

        if parent_node is None:
            # Родительский путь не существует
            return None
        
        if parent_node['type'] != 'dir':
            # Родительский узел не является директорией (нельзя создать файл внутри файла)
            return None
        
        # 2. Проверяем, существует ли узел уже
        if name in parent_node['children']:
            # Если узел уже существует, команда touch просто обновляет его
            # (в нашем случае возвращаем пустой узел)
            existing_node = parent_node['children'][name]
            if existing_node['type'] == 'dir' and node_type == 'file':
                # нельзя переписать директорию файлом
                return None
            return existing_node

        # 3. создаём новый узел
        new_node = {'type': node_type}
        if node_type == 'file':
            new_node['content'] = content if content != None else ""
        elif node_type == 'dir':
            new_node['children'] = {}

        parent_node['children'][name] = new_node
        return new_node

def get_home_dir():
    return os.getenv('HOME') or os.getenv('USERPROFILE')

def commParser(comm):
    command_history.append(comm.strip()) # strip() удаляет лишние пробелы. пример: "   ls -l" -> "ls -l"

    parts = shlex.split(comm) # создаём список из введённой команды. умное разделение, считает всё в кавычках как один элемент, пробелами разделяет элементы
    if len(parts) == 0:
        return None, []
    command = parts[0] # берём первый элемент из списка
    args = parts[1:] # берём все аргументы (список, начиная со второго элемента)

    processed_args = []

    for arg in args: # запускаем обработку команд и, если нужно, подставляем переменные окружения в аргументы команды
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

def date_comm(args):
    # выводит текущую дату и время
    now = datetime.now()
    print(now.strftime("%a %b %d %H: %M: %S: %Z %Y")) # строка %день недели %сокращённое название месяца %день месяца %час в 24 часовом формате %минуты %секунды %временная зона(в Windows может быть пусто) %год

def history_comm(args):
    # выводит список ранее введённых команд
    if not command_history:
        print("История команд пуста")
        return
    
    # выводим историю, нумеруя с 1
    for i, cmd in enumerate(command_history, 1):
        if cmd and not cmd.startswith('#'):
            print(f"{i: 4} {cmd}") #i: 4 - выводимое число i занимает минимум 4 символа в ширину
            # history_comm может выводить себя, так как она тоже была введена

def _print_tree_recursive(node, prefix, vfs, path_parts):
    # рекурсивная функция для отрисовки дерева
    # получаем имена дочерних элементов и сортируем их
    children_names = sorted(node.get('children', {}).keys())

    for i, name in enumerate(children_names):
        is_last = (i == len(children_names)-1)
        
        #выбираем правильный символ для ветки
        branch = "└── " if is_last else "├── "

        # рекурсивеый префикс для отступов
        next_prefix = prefix + ("    " if is_last else "|   ")

        child_node = node['children'][name]

        # формируем полный путь для отображения
        full_path = path_parts + [name]

        # вывод текущего элемента
        print(f"{prefix}{branch}{name}")

        # если это директория, рекурсивно вызываем для её содержимого
        if child_node['type'] == 'dir':
            _print_tree_recursive(child_node, next_prefix, vfs, full_path)

def tree_comm(args, vfs):
    # выводит содержимое директории в виде дерева
    path = args[0] if args else None

    if path == None:
        target_path_parts = vfs.current_path
    else:
        target_path_parts = vfs._normalize_path(path)

    target_dir = vfs._find_node(target_path_parts)

    if target_dir == None:
        print(f"tree: '{path}': No such file or directory")
        return
    
    if target_dir['type'] != 'dir':
        print(f"tree: '{path}' is not a directory")
        return

    # отображаем имя стартовой директории
    start_dir_name = "/" if not target_path_parts else target_path_parts[-1]
    print(start_dir_name)

    # запускаем рекурсивный обход
    _print_tree_recursive(target_dir, "", vfs, target_path_parts) 

def touch_comm(args, vfs):
    # создаёт файл, если он не существует
    if not args:
        print("touch: требуется операнд файла")
        return
    
    path_str = args[0]

    target_path_parts = vfs._normalize_path(path_str)

    if not target_path_parts:
        print("touch: неверный путь")
        return
    
    # создаём (или находим) узел
    # touch создаёт файл, поэтому node_type='file'
    result_node = vfs._create_node(target_path_parts, 'file', content="")

    if result_node is None:
        print(f"touch: невозможно создать файл '{path_str}': no such file or directory or target is directory")
    else:
        pass # успех

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


def main():
    parser = argparse.ArgumentParser(description="Эмулятор языка оболочки ОС (VFS Shell)") # создаём объект, который будет отвечать за обработку аргументов, переданных программе через командную строку

    # добавляем команды в объект парсер
    # путь к физическому расположение VFS
    parser.add_argument('-v', '--vfs-path', 
                        required=True, # теперь путь к CSV обязателен 
                        help='Путь к CSV-файлу с описанием VFS')
    
    parser.add_argument('-s', '--script', 
                        default=None, 
                        help='Путь к стартовому скрипту для выполнения команд')
    
    args = parser.parse_args() # считываем аргументы. в args будет объект, у которого аргументы будут храниться в виде атрибутов, названных по длинным именам аргументов

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

    # лямбда-функции, которые получают аргументы и передают их в вызываемые функции
    commands = {
    'ls' : lambda a: ls_comm(a, vfs),
    'cd' : lambda a: cd_comm(a, vfs),
    'date' : date_comm,
    'history' : history_comm,
    'tree' : lambda a: tree_comm(a, vfs),
    'touch' : lambda a: touch_comm(a, vfs),
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