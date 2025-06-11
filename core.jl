using UUIDs

@enum Status not_started in_progress finished

struct Task
    id::UUID
    description::String
    status::Status
end


function addTask(tasks::Vector{Task}, description::String)::Vector{Task}
    newTask = Task(uuid4(), description, not_started)
    return [tasks..., newTask]
end

function removeTask(tasks::Vector{Task}, id::UUID)::Vector{Task}
    return filter(task -> task.id != id, tasks)
end

function changeStatus(tasks::Vector{Task}, id::UUID, newStatus::Status)::Tuple{Vector{Task}, Bool}
    if newStatus == in_progress
        inProgressCount = count(task -> task.status == in_progress, tasks)
        if inProgressCount >= 5
            println("Помилка: Не можна мати більше 5 завдань у статусі 'в процесі'.")
            return (tasks, false)
        end
    end
    
    newTasks = map(tasks) do task
        if task.id == id
            return Task(task.id, task.description, newStatus)
        else
            return task
        end
    end
    
    return (newTasks, true)
end

function showTasks(tasks::Vector{Task})
    if isempty(tasks)
        println("Список завдань порожній.")
        return
    end
    
    println("\n--- Список Завдань ---")
    for task in tasks
        println("ID: $(task.id)")
        println("  Опис: $(task.description)")
        println("  Статус: $(task.status)")
        println("-"^20)
    end
end

# core.jl - Додайте цей код в кінець файлу

# ... (весь ваш попередній код Task, Status, addTask і т.д.) ...

# 4. ФУНКЦІЯ ДЛЯ ВІДНОВЛЕННЯ СТАНУ З ДАНИХ
# Ця функція буде викликатись з Python для уникнення проблем з типами.
"""
    buildTasksFromData(data::Vector)

Приймає вектор (отриманий з Python), де кожен елемент є словником, 
і створює з нього строго типізований вектор Vector{Task}.
"""
function buildTasksFromData(data::Vector)::Vector{Task}
    # Створюємо порожній, але правильно типізований вектор
    tasks = Vector{Task}()
    
    for item in data
        # Конвертуємо дані, що прийшли з Python
        task_uuid = UUIDs.UUID(item["id"])
        task_status = Status(item["status"]) 
        description = item["description"]
        
        new_task = Task(task_uuid, description, task_status)
        
        # Наповнюємо наш вектор, не виходячи з середовища Julia
        push!(tasks, new_task)
    end
    
    return tasks
end

# core.jl - Додайте цей код в кінець файлу

# ... (весь ваш попередній код) ...

# 5. ФУНКЦІЯ-ДИСПЕТЧЕР ДЛЯ ВИКЛИКІВ З PYTHON
# Це єдина точка входу, яка вирішує проблему втрати типів.
"""
    call_with_typed_state(func_name::String, state::Vector, args...)

Приймає назву функції, вектор стану (який приходить як Vector{Any}) та інші аргументи.
Примусово конвертує стан до Vector{Task} і викликає справжню функцію.
"""
function call_with_typed_state(func_name::String, state::Vector, args...)
    # Це найважливіший рядок у всьому проекті.
    # Він перетворює нетипізований вектор з Python у строго типізований вектор Julia.
    typed_state = Vector{Task}(state)
    
    # Отримуємо посилання на реальну функцію за її назвою (символом)
    func_to_call = getfield(Main, Symbol(func_name))
    
    # Викликаємо реальну функцію з уже правильними типами
    return func_to_call(typed_state, args...)
end