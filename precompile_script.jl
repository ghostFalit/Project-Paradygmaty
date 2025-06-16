include("core.jl")
using UUIDs
using JSON

println("Starting precompilation of functions...")

let
    tasks = Vector{TaskItem}()
    
    tasks = call_with_typed_state("addTask", tasks, "Test Task")
    
    if !isempty(tasks)
        task_id = tasks[1].id
        tasks, _ = call_with_typed_state("changeStatus", tasks, task_id, in_progress)
        tasks = call_with_typed_state("removeTask", tasks, task_id)
    end
    
    serialized = serialize_tasks(tasks) 
    json_string = JSON.json(serialized)
    build_tasks_from_json(json_string) 

    call_with_typed_state("showTasks", tasks)
end

println("Precompilation finished.")