using Replay

animation = joinpath(@__DIR__, "animation.jl")

# Load the ANSI cursor helpers from a source file. Pasting their multiline,
# escape-heavy definitions through interactive line editing is not portable.
instructions = [
    "using UnicodePlots",
    "include($(repr(animation)))",
    "frames = [lineplot(x -> sin(x - t), width = 40) for t = -2π:0.25π:2π];",
    "animate(frames)",
]

replay(instructions; julia_project=@__DIR__, use_ghostwriter=false)
