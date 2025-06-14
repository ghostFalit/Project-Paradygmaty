# precompile_script.jl (English version)

include("core.jl")
using UUIDs
using JSON

println("Starting precompilation of functions...")

let
    tasks = Vector{TaskItem}()
    
    tasks = addTask(tasks, "Compilation test task")
    
    if !isempty(tasks)
        task_id = tasks[1].id
        tasks, _ = changeStatus(tasks, task_id, in_progress)
    end
    
    serialized = serialize_tasks(tasks)
    json_string = JSON.json(serialized)
    build_tasks_from_json(json_string)
    
    if !isempty(tasks)
        task_id = tasks[1].id
        tasks = removeTask(tasks, task_id)
    end

    showTasks(tasks)
end

println("Precompilation finished.")