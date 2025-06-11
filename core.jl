# core.jl (фінальна версія 2.0)
using UUIDs
using JSON

@enum Status not_started in_progress finished

struct Task
    id::UUID
    description::String
    status::Status
end

# <-- ДОДАНО: Нова функція для серіалізації -->
"""
    serialize_tasks(tasks::Vector{Task})::Vector{Dict{String, Any}}

Перетворює вектор завдань на вектор словників з простими типами,
готовий для збереження у JSON. Це "чиста" функція Julia.
"""
function serialize_tasks(tasks::Vector{Task})::Vector{Dict{String, Any}}
    serializable_tasks = []
    for task in tasks
        push!(serializable_tasks, Dict(
            "id" => string(task.id), # Правильна конвертація UUID -> String в Julia
            "description" => task.description,
            "status" => Int(task.status) # Конвертація Enum -> Int
        ))
    end
    return serializable_tasks
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
            println("Błąd: Nie można mieć więcej niż 5 zadań w statusie 'w toku'.")
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
        println("Lista zadań jest pusta.")
        return
    end
    
    println("\n--- Lista Zadań ---")
    for task in tasks
        println("ID: $(task.id)")
        println("  Opis: $(task.description)")
        println("  Status: $(task.status)")
        println("-"^20)
    end
end

function build_tasks_from_json(json_string::String)::Vector{Task}
    tasks = Vector{Task}()
    data = JSON.parse(json_string)
    
    for item in data
        task_uuid = UUIDs.UUID(item["id"])
        description = item["description"]
        task_status = Status(item["status"])
        
        new_task = Task(task_uuid, description, task_status)
        push!(tasks, new_task)
    end
    
    return tasks
end

function call_with_typed_state(func_name::String, state::Vector, args...)
    typed_state = Vector{Task}(state)
    func_to_call = getfield(Main, Symbol(func_name))
    return func_to_call(typed_state, args...)
end