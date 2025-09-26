import os
import shlex
import argparse

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
            home_dir = get_home_dir()
            if home_dir:
                processed_args.append(home_dir)
            else:
                print("Ошибка: не удалось определить домашнюю директорию.")
                processed_args.append(arg)
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
def ls_comm(args):
    print(f"команда 'ls' вызвана с аргументами: {args}")

def cd_comm(args):
    print(f"команда 'cd' вызвана с аргументами {args}")

def exit_comm(args):
    print("Выход из программы.")
    raise SystemExit

commands = {
    'ls' : ls_comm,
    'cd' : cd_comm,
    'exit' : exit_comm
}

def main():
    parser = argparse.ArgumentParser(description="Эмулятор языка оболочки ОС (VFS Shell)")

    # путь к физическому расположение VFS
    parser.add_argument('-v', '--vfs-path', 
                        default='./vfs', # значение по умолчанию 
                        help='Путь к физическому расположению VFS')
    
    parser.add_argument('-s', '--script', 
                        default=None, 
                        help='Путь к стартовому скрипту для выполнения команд')
    
    args = parser.parse_args()

    print("--- Параметры запуска ---")
    print(f"VFS Path:{args.vfs_path}")
    print(f"Start Script:{args.script}")

    # Логика запуска: Скрипт или REPL
    if args.script:
        execute_script(args.script, commands)
        return
    else:
        while True:
            try:
                user_input = input("VFS>")
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