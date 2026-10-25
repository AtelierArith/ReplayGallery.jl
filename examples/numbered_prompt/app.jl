using Replay

# Use Julia's real prompt rather than the simulated ghostwriter prompt.
# REPL.numbered_prompt! is available on the supported Julia LTS/stable releases.
replay(
    ["1 + 1", "ans * 3", "Out[1]"],
    use_ghostwriter=false,
    startup_prompt="In [1]: ",
    prompt_delimiter="]: ",
    cmd=`--color=yes -e 'using REPL; atreplinit() do repl; repl.interface = REPL.setup_interface(repl); REPL.numbered_prompt!(repl); end'`,
)
