# main.py (фінальна версія 2.0)

import os
import json
from julia.api import Julia

# --- Ініціалізація мосту з Julia ---
print("Inicjalizacja środowiska Julii...")
jl = Julia(compiled_modules=False)

# --- Завантаження функціонального ядра та отримання доступу до його об'єктів ---
print("Ładowanie jądra funkcyjnego...")
jl.eval('include("core.jl")')

class JuliaCore:
    def __init__(self, julia_instance):
        self.build_tasks_from_json = julia_instance.eval("build_tasks_from_json")
        self.call = julia_instance.eval("call_with_typed_state")
        # <-- ДОДАНО: Посилання на нову функцію серіалізації -->
        self.serialize_tasks = julia_instance.eval("serialize_tasks")

Core = JuliaCore(jl)
print("Jądro załadowane. Aplikacja gotowa do pracy.")


STATE_FILE = "tasks.json"

# --- Функції для роботи зі станом (збереження/завантаження) ---

# <-- ЗМІНЕНО: Повністю переписана функція save_state -->
def save_state(state):
    """Зберігає стан, делегуючи підготовку даних до Julia."""
    # Якщо стан порожній, просто створюємо порожній список
    if jl.eval('length')(state) == 0:
        py_state = []
    else:
        # 1. Викликаємо функцію Julia, щоб отримати "чисті" дані
        # Результат буде звичайним списком словників Python
        py_state = Core.serialize_tasks(state)
    
    # 2. Зберігаємо ці чисті дані у JSON
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(py_state, f, indent=4, ensure_ascii=False)

def load_state():
    """Завантажує стан, передаючи дані як JSON-рядок до Julia."""
    empty_state = jl.eval("Vector{Task}()")
    if not os.path.exists(STATE_FILE):
        return empty_state

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        if not content or len(content) < 5:
            return empty_state
            
    julia_state = Core.build_tasks_from_json(content)
    
    num_tasks = jl.eval('length')(julia_state)
    print(f"Załadowano {num_tasks} zadań.")
    return julia_state


# --- Решта коду залишається без змін ---
# (вставте сюди решту функцій: display_menu, handle_..., main)
def display_menu():
    print("\n--- Menu ---")
    print("1. Pokaż wszystkie zadania")
    print("2. Dodaj zadanie")
    print("3. Zmień status zadania")
    print("4. Usuń zadanie")
    print("5. Wyjdź")

def handle_show_tasks(state):
    Core.call("showTasks", state)

def handle_add_task(state):
    new_state = Core.call("addTask", state, input("Wprowadź opis zadania: "))
    print("Zadanie pomyślnie dodane.")
    return new_state

def handle_change_status(state):
    if jl.eval('length')(state) == 0:
        print("Lista zadań jest pusta.")
        return state

    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (Status: {task.status})")
    
    try:
        task_idx = int(input("Podaj numer zadania, aby zmienić status: ")) - 1
        task_to_change = state[task_idx]

        print("Wybierz nowy status: 0 - nierozpoczęte, 1 - w toku, 2 - zakończone")
        status_idx = int(input("Podaj numer statusu: "))
        if not (0 <= status_idx <= 2):
            print("Błąd: nieprawidłowy numer statusu.")
            return state

        task_id = task_to_change.id
        new_status = jl.eval("Status")(status_idx)
        
        result_tuple = Core.call("changeStatus", state, task_id, new_status)
        new_state, success = result_tuple[0], result_tuple[1]

        if success:
            print("Status pomyślnie zmieniony.")
            return new_state
        else:
            return state
    except (ValueError, IndexError):
        print("Błąd: wprowadź poprawną liczbę.")
        return state

def handle_remove_task(state):
    if jl.eval('length')(state) == 0:
        print("Lista zadań jest pusta.")
        return state

    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (ID: {task.id})")

    try:
        task_idx = int(input("Podaj numer zadania do usunięcia: ")) - 1
        task_to_remove = state[task_idx]
        task_id = task_to_remove.id
        
        new_state = Core.call("removeTask", state, task_id)
        print("Zadanie pomyślnie usunięte.")
        return new_state
    except (ValueError, IndexError):
        print("Błąd: wprowadź poprawną liczbę.")
        return state

def main():
    app_state = load_state()

    while True:
        display_menu()
        choice = input("Twój wybór: ")

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
            print("Zakończenie pracy.")
            break
        else:
            print("Nieprawidłowy wybór. Spróbuj ponownie.")

if __name__ == "__main__":
    main()