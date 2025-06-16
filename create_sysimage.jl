using PackageCompiler

sysimage_path = "TaskPlannerSysimage"

create_sysimage(
    [:UUIDs, :JSON];
    sysimage_path=sysimage_path,
    precompile_execution_file="precompile_script.jl"
)