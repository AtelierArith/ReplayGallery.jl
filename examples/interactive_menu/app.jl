using Replay

# Each menu request and its response must be separate instructions.
# Carriage return confirms selection; q cancels without terminating the REPL.
replay([
    "using REPL.TerminalMenus",
    "menu = RadioMenu([\"apple\", \"orange\"]);",
    "choice = request(\"Choose fruit:\", menu)",
    "$(DOWN_ARROW)\r",
    "@assert choice == 2; @show choice",
    "cancelled = request(\"Cancel this menu:\", RadioMenu([\"apple\", \"orange\"]))",
    "q",
    "@assert cancelled == -1; @show cancelled",
    "again = request(\"Choose again:\", RadioMenu([\"apple\", \"orange\"]))",
    "\r",
    "@assert again == 1; @show again",
]; use_ghostwriter=false)
