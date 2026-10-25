using Pkg, TOML
root = dirname(@__DIR__)
source = TOML.parsefile(joinpath(root, "replay-source.toml"))
project = joinpath(root, "Project.toml")
original = read(project, String)
try
    Pkg.activate(root)
    # REPLAY_PATH is for testing an explicitly selected local core checkout only.
    if haskey(ENV, "REPLAY_PATH")
        Pkg.develop(path=abspath(ENV["REPLAY_PATH"]))
    else
        Pkg.add(PackageSpec(url=source["url"], rev=source["rev"]))
    end
    Pkg.instantiate()
finally
    # New Julia versions persist [sources]; keep local paths out of tracked inputs.
    write(project, original)
end
