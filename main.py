# main.py (English version with low-level warning suppression)

import os
import json
import sys

# --- Powerful Julia initialization with warning suppression ---
# This block uses low-level redirection of the error stream
# at the OS level, which is guaranteed to hide the warnings.

print("Initializing Julia environment from system image...")

# 1. Save the original stderr file descriptor
original_stderr_fd = os.dup(sys.stderr.fileno())

# 2. Open the "black hole" (os.devnull)
devnull_fd = os.open(os.devnull, os.O_WRONLY)

try:
    # 3. Redirect stderr to devnull
    os.dup2(devnull_fd, sys.stderr.fileno())
    
    # 4. Execute the code that generates warnings
    from julia.api import Julia
    jl = Julia(sysimage="TaskPlannerSysimage.exe")

finally:
    # 5. IMPORTANT: Restore the original error stream no matter what
    os.dup2(original_stderr_fd, sys.stderr.fileno())
    
    # 6. Close the file descriptors we opened
    os.close(devnull_fd)
    os.close(original_stderr_fd)


# --- Loading the functional core and getting access to its objects ---
print("Loading functional core...")
jl.eval('include("core.jl")')

# A wrapper class for convenient access to Julia functions
class JuliaCore:
    def __init__(self, julia_instance):
        self.build_tasks_from_json = julia_instance.eval("build_tasks_from_json")
        self.serialize_tasks = julia_instance.eval("serialize_tasks")
        self.call = julia_instance.eval("call_with_typed_state")
        self.json_serializer = julia_instance.eval("JSON.json")
        self.length = julia_instance.eval("length")
        self.Status = julia_instance.eval("Status")

Core = JuliaCore(jl)
print("Core loaded. Application is ready.")


STATE_FILE = "tasks.json"

# --- Functions for state management (save/load) ---

def save_state(state):
    """Saves the state using the serialize_tasks function from Julia."""
    serializable_list = Core.serialize_tasks(state)
    json_string = Core.json_serializer(serializable_list)
    
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(json_string)

def load_state():
    """Loads the state by passing the JSON string to Julia for processing."""
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
        print(f"Loaded {num_tasks} tasks.")
        return julia_state
    except Exception as e:
        print(f"Error loading state: {e}")
        print("Created a new, empty state.")
        return empty_state

# --- User interaction functions ---

def display_menu():
    print("\n--- Menu ---")
    print("1. Show all tasks")
    print("2. Add a task")
    print("3. Change a task's status")
    print("4. Remove a task")
    print("5. Exit")

def handle_show_tasks(state):
    Core.call("showTasks", state)

def handle_add_task(state):
    description = input("Enter the task description: ")
    new_state = Core.call("addTask", state, description)
    print("Task added successfully.")
    return new_state

def handle_change_status(state):
    if Core.length(state) == 0:
        print("The task list is empty.")
        return state

    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (Status: {task.status})")
    
    try:
        task_idx = int(input("Enter the number of the task to change status: ")) - 1
        task_to_change = state[task_idx]

        print("Select new status: 0 - Not Started, 1 - In Progress, 2 - Finished")
        status_idx = int(input("Enter the status number: "))
        if not (0 <= status_idx <= 2):
            print("Error: invalid status number.")
            return state

        task_id = task_to_change.id
        new_status = Core.Status(status_idx)
        
        result_tuple = Core.call("changeStatus", state, task_id, new_status)
        new_state, success = result_tuple[0], result_tuple[1]

        if success:
            print("Status changed successfully.")
            return new_state
        else:
            # The error message is printed by the Julia core
            return state
    except (ValueError, IndexError):
        print("Error: please enter a valid number.")
        return state

def handle_remove_task(state):
    if Core.length(state) == 0:
        print("The task list is empty.")
        return state

    for i, task in enumerate(state):
        print(f"{i+1}. {task.description} (ID: {task.id})")

    try:
        task_idx = int(input("Enter the number of the task to remove: ")) - 1
        task_to_remove = state[task_idx]
        task_id = task_to_remove.id
        
        new_state = Core.call("removeTask", state, task_id)
        print("Task removed successfully.")
        return new_state
    except (ValueError, IndexError):
        print("Error: please enter a valid number.")
        return state

def main():
    app_state = load_state()

    while True:
        display_menu()
        choice = input("Your choice: ")

        if choice == '1':
            handle_show_tasks(app_state)
        elif choice == '2':
            app_state = handle_add_task(app_state)
            save_state(app_state)
        elif choice == '3':
            old_state_repr = Core.json_serializer(Core.serialize_tasks(app_state))
            app_state = handle_change_status(app_state)
            new_state_repr = Core.json_serializer(Core.serialize_tasks(app_state))
            if old_state_repr != new_state_repr:
                save_state(app_state)
        elif choice == '4':
            app_state = handle_remove_task(app_state)
            save_state(app_state)
        elif choice == '5':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()