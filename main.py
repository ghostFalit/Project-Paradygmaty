# main.py - Імперативна оболонка для управління планувальником (фінальна, робоча версія)

import os
import json
from julia.api import Julia

# --- Ініціалізація мосту з Julia ---
print("Ініціалізація середовища Julia...")
jl = Julia(compiled_modules=False)

# --- Завантаження функціонального ядра та отримання доступу до його об'єктів ---
print("Завантаження функціонального ядра...")
jl.eval('include("core.jl")')

class JuliaCore:
    def __init__(self, julia_instance):
        # Отримуємо посилання на функцію-конструктор і диспетчер
        self.buildTasksFromData = julia_instance.eval("buildTasksFromData")
        self.call = julia_instance.eval("call_with_typed_state")
        
        # <<< ЗМІНЕНО: Додаємо посилання на функцію Int з Julia для конвертації
        self.Int = julia_instance.eval("Int")

Core = JuliaCore(jl)
print("Ядро завантажено. Додаток готовий до роботи.")


STATE_FILE = "tasks.json"

# --- Функції для роботи зі станом (збереження/завантаження) ---

def save_state(state):
    """Зберігає стан, використовуючи функцію Int з Julia для конвертації enum."""
    py_state = []
    if jl.eval('length')(state) > 0:
        for task in state:
            py_state.append({
                "id": str(task.id),
                "description": task.description,
                # <<< ЗМІНЕНО: Використовуємо Core.Int замість int()
                "status": Core.Int(task.status) 
            })
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(py_state, f, indent=4, ensure_ascii=False)

def load_state():
    """Завантажує стан, передаючи дані для обробки в Julia."""
    empty_state = jl.eval("Vector{Task}()")
    if not os.path.exists(STATE_FILE):
        return empty_state

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            if os.path.getsize(STATE_FILE) < 5:
                return empty_state
            py_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return empty_state

    if not py_data:
        return empty_state
        
    julia_state = Core.buildTasksFromData(py_data)
    num_tasks = jl.eval('length')(julia_state)
    print(f"Завантажено {num_tasks} завдань.")
    return julia_state

# --- Решта коду залишається без змін ---

def display_menu():
    print("\n--- Меню ---")
    print("1. Показати всі завдання")
    print("2. Додати завдання")
    print("3. Змінити статус завдання")
    print("4. Видалити завдання")
    print("5. Вийти")

def handle_show_tasks(state):
    Core.call("showTasks", state)

def handle_add_task(state):
    new_state = Core.call("addTask", state, input("Введіть опис завдання: "))
    print("Завдання успішно додано.")
    return new_state

def handle_change_status(state):
    if jl.eval('length')(state) == 0:
        print("Список завдань порожній.")
        return state

    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (Статус: {task.status})")
    
    try:
        task_idx = int(input("Введіть номер завдання для зміни статусу: ")) - 1
        task_to_change = state[task_idx]

        print("Виберіть новий статус: 0 - не почата, 1 - в процесі, 2 - закінчена")
        status_idx = int(input("Введіть номер статусу: "))
        if not (0 <= status_idx <= 2):
            print("Помилка: невірний номер статусу.")
            return state

        task_id = task_to_change.id
        new_status = jl.eval("Status")(status_idx)
        
        result_tuple = Core.call("changeStatus", state, task_id, new_status)
        new_state, success = result_tuple[0], result_tuple[1]

        if success:
            print("Статус успішно змінено.")
            return new_state
        else:
            return state
    except (ValueError, IndexError):
        print("Помилка: введіть коректне число.")
        return state

def handle_remove_task(state):
    if jl.eval('length')(state) == 0:
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
        print("Помилка: введіть коректне число.")
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
            old_state = app_state
            app_state = handle_change_status(app_state)
            if app_state is not old_state:
                save_state(app_state)
        elif choice == '4':
            app_state = handle_remove_task(app_state)
            save_state(app_state)
        elif choice == '5':
            print("Завершення роботи.")
            break
        else:
            print("Невірний вибір. Спробуйте ще раз.")

if __name__ == "__main__":
    main()