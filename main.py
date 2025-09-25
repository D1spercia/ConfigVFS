import os
import shlex

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