# core.jl (English version)
using UUIDs
using JSON

@enum Status not_started in_progress finished

# RENAMED: The struct was renamed to avoid conflict with Julia's built-in `Task` type.
struct TaskItem
    id::UUID
    description::String
    status::Status
end

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
            println("Error: Cannot have more than 5 tasks 'in progress'.")
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
        println("The task list is empty.")
        return
    end
    
    println("\n--- Task List ---")
    for task in tasks
        println("ID: $(task.id)")
        println("  Description: $(task.description)")
        println("  Status: $(task.status)")
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

# A helper function to ensure the state vector has the correct type before calling other functions.
function call_with_typed_state(func_name::String, state::Vector, args...)
    typed_state = Vector{TaskItem}(state)
    func_to_call = getfield(Main, Symbol(func_name))
    return func_to_call(typed_state, args...)
end