# create_sysimage.jl
using PackageCompiler

# Path to the system image. PackageCompiler will determine the extension (.dll/.so)
sysimage_path = "TaskPlannerSysimage"

create_sysimage(
    [:UUIDs, :JSON];
    sysimage_path=sysimage_path,
    precompile_execution_file="precompile_script.jl"
)