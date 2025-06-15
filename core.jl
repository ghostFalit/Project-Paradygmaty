# core.jl (Фінальна українська версія з функцією-шлюзом)
using UUIDs
using JSON

@enum Status not_started in_progress finished

struct TaskItem
    id::UUID
    description::String
    status::Status
end

# --- Функція-шлюз, що вирішує проблему типів ---
# Вона приймає будь-який вектор з Python, приводить його до потрібного типу
# і викликає відповідну функцію.
function call_with_typed_state(func_name::String, state::Vector, args...)
    typed_state = Vector{TaskItem}(state)
    func_to_call = getfield(Main, Symbol(func_name))
    return func_to_call(typed_state, args...)
end

# --- Основні функції ядра (залишаються без змін) ---

function serialize_tasks(tasks::Vector{TaskItem})::Vector{Dict{String, Any}}
    serializable_tasks = []
    for task in tasks
        push!(serializable_tasks, Dict(
            "id" => string(task.id),
            "description" => task.description,
            "status" => Int(task.status)
        ))
    end
    return serializable_tasks
end

function addTask(tasks::Vector{TaskItem}, description::String)::Vector{TaskItem}
    newTask = TaskItem(uuid4(), description, not_started)
    return [tasks..., newTask]
end

function removeTask(tasks::Vector{TaskItem}, id::UUID)::Vector{TaskItem}
    return filter(task -> task.id != id, tasks)
end

function changeStatus(tasks::Vector{TaskItem}, id::UUID, newStatus::Status)::Tuple{Vector{TaskItem}, Bool}
    if newStatus == in_progress
        inProgressCount = count(task -> task.status == in_progress, tasks)
        if inProgressCount >= 5
            println("Помилка: Не можна мати більше 5 завдань у статусі 'в процесі'.")
            return (tasks, false)
        end
    end
    
    newTasks = map(tasks) do task
        if task.id == id
            return TaskItem(task.id, task.description, newStatus)
        else
            return task
        end
    end
    
    return (newTasks, true)
end

function showTasks(tasks::Vector{TaskItem})
    if isempty(tasks)
        println("Список завдань порожній.")
        return
    end
    
    println("\n--- Список завдань ---")
    for task in tasks
        println("ID: $(task.id)")
        println("  Опис: $(task.description)")
        println("  Статус: $(task.status)")
        println("-"^20)
    end
end

function build_tasks_from_json(json_string::String)::Vector{TaskItem}
    tasks = Vector{TaskItem}()
    data = JSON.parse(json_string)
    
    for item in data
        task_uuid = UUIDs.UUID(item["id"])
        description = item["description"]
        task_status = Status(item["status"])
        
        new_task = TaskItem(task_uuid, description, task_status)
        push!(tasks, new_task)
    end
    
    return tasks
end