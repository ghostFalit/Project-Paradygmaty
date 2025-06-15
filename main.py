# main.py (Фінальна українська версія, використовує функцію-шлюз)

import os
import json
import sys

# --- Ініціалізація Julia з приховуванням попереджень ---
print("Ініціалізація середовища Julia з образу системи...")
original_stderr_fd = os.dup(sys.stderr.fileno())
devnull_fd = os.open(os.devnull, os.O_WRONLY)
try:
    os.dup2(devnull_fd, sys.stderr.fileno())
    from julia.api import Julia
    jl = Julia(sysimage="TaskPlannerSysimage.exe")
finally:
    os.dup2(original_stderr_fd, sys.stderr.fileno())
    os.close(devnull_fd)
    os.close(original_stderr_fd)

# --- Завантаження функціонального ядра ---
print("Завантаження функціонального ядра...")
jl.eval('include("core.jl")')

# <<< ЗМІНЕНО: Тепер нам потрібні лише кілька ключових функцій >>>
class JuliaCore:
    def __init__(self, julia_instance):
        # Функція-шлюз для всіх операцій зі станом
        self.call = julia_instance.eval("call_with_typed_state")
        
        # Окремі функції, що не приймають стан або працюють з JSON
        self.build_tasks_from_json = julia_instance.eval("build_tasks_from_json")
        self.serialize_tasks = julia_instance.eval("serialize_tasks")
        self.json_serializer = julia_instance.eval("JSON.json")
        self.length = julia_instance.eval("length")
        self.Status = julia_instance.eval("Status")

Core = JuliaCore(jl)
print("Ядро завантажено. Додаток готовий до роботи.")

STATE_FILE = "tasks.json"

# --- Функції для роботи зі станом ---

def save_state(state):
    # Ця перевірка залишається, вона надійна
    if Core.length(state) == 0:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return

    serializable_list = Core.serialize_tasks(state)
    json_string = Core.json_serializer(serializable_list)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(json_string)

def load_state():
    empty_state = jl.eval("Vector{TaskItem}()")
    if not os.path.exists(STATE_FILE):
        return empty_state
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        json_string = f.read()
        if not json_string:
            return empty_state
    try:
        julia_state = Core.build_tasks_from_json(json_string)
        num_tasks = Core.length(julia_state)
        print(f"Завантажено {num_tasks} завдань.")
        return julia_state
    except Exception as e:
        print(f"Помилка завантаження стану: {e}")
        print("Створено новий, порожній стан.")
        return empty_state

# --- Функції для взаємодії з користувачем (використовують 'Core.call') ---

def display_menu():
    print("\n--- Меню ---")
    print("1. Показати всі завдання")
    print("2. Додати завдання")
    print("3. Змінити статус завдання")
    print("4. Видалити завдання")
    print("5. Очистити всі завдання")
    print("6. Вийти")

def handle_show_tasks(state):
    Core.call("showTasks", state)

def handle_add_task(state):
    description = input("Введіть опис завдання: ")
    new_state = Core.call("addTask", state, description)
    print("Завдання успішно додано.")
    return new_state

def handle_change_status(state):
    if Core.length(state) == 0:
        print("Список завдань порожній.")
        return state
    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (Статус: {task.status})")
    try:
        task_idx = int(input("Введіть номер завдання для зміни статусу: ")) - 1
        task_to_change = state[task_idx]
        print("Виберіть новий статус: 0 - Не розпочато, 1 - В процесі, 2 - Завершено")
        status_idx = int(input("Введіть номер статусу: "))
        if not (0 <= status_idx <= 2):
            print("Помилка: невірний номер статусу.")
            return state
        task_id = task_to_change.id
        new_status = Core.Status(status_idx)
        result_tuple = Core.call("changeStatus", state, task_id, new_status)
        new_state, success = result_tuple[0], result_tuple[1]
        if success:
            print("Статус успішно змінено.")
            return new_state
        else:
            return state
    except (ValueError, IndexError):
        print("Помилка: будь ласка, введіть правильний номер.")
        return state

def handle_remove_task(state):
    if Core.length(state) == 0:
        print("Список завдань порожній.")
        return state
    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (ID: {task.id})")
    try:
        task_idx = int(input("Введіть номер завдання для видалення: ")) - 1
        task_to_remove = state[task_idx]
        task_id = task_to_remove.id
        new_state = Core.call("removeTask", state, task_id)
        print("Завдання успішно видалено.")
        return new_state
    except (ValueError, IndexError):
        print("Помилка: будь ласка, введіть правильний номер.")
        return state

def handle_clear_all_tasks(state):
    if Core.length(state) == 0:
        print("Список завдань вже порожній.")
        return state
    
    confirm = input("Ви впевнені, що хочете видалити ВСІ завдання? Цю дію неможливо скасувати. (так/ні): ").lower().strip()
    
    if confirm == 'так':
        print("Всі завдання було успішно видалено.")
        return jl.eval("Vector{TaskItem}()")
    else:
        print("Операцію скасовано.")
        return state

def main():
    app_state = load_state()

    while True:
        display_menu()
        choice = input("Ваш вибір: ")

        if choice == '1':
            handle_show_tasks(app_state)
        elif choice == '2':
            app_state = handle_add_task(app_state)
            save_state(app_state)
        elif choice == '3':
            old_state_repr = Core.json_serializer(Core.serialize_tasks(app_state))
            app_state = handle_change_status(app_state)
            # Перевірка на випадок, якщо операція не вдалася
            if Core.length(app_state) > 0 or old_state_repr != "[]":
                 new_state_repr = Core.json_serializer(Core.serialize_tasks(app_state))
                 if old_state_repr != new_state_repr:
                    save_state(app_state)
            else: # Якщо стан став порожнім
                 save_state(app_state)
        elif choice == '4':
            app_state = handle_remove_task(app_state)
            save_state(app_state)
        elif choice == '5':
            app_state = handle_clear_all_tasks(app_state)
            save_state(app_state)
        elif choice == '6':
            print("Завершення роботи.")
            break
        else:
            print("Невірний вибір. Спробуйте ще раз.")

if __name__ == "__main__":
    main()