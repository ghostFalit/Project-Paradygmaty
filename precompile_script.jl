# precompile_script.jl (Фінальна українська версія)

include("core.jl")
using UUIDs
using JSON

println("Запуск попередньої компіляції функцій...")

let
    tasks = Vector{TaskItem}()
    
    # Використовуємо шлюз для компіляції
    tasks = call_with_typed_state("addTask", tasks, "Тестове завдання")
    
    if !isempty(tasks)
        task_id = tasks[1].id
        tasks, _ = call_with_typed_state("changeStatus", tasks, task_id, in_progress)
        tasks = call_with_typed_state("removeTask", tasks, task_id)
    end
    
    serialized = serialize_tasks(tasks) # Цю можна залишити, бо вона не змінює стан
    json_string = JSON.json(serialized)
    build_tasks_from_json(json_string) # І цю

    call_with_typed_state("showTasks", tasks)
end

println("Попередня компіляція завершена.")