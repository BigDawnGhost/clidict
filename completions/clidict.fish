# Fish tab-completion for clidict
# Install: copy or symlink to ~/.config/fish/completions/clidict.fish
#
#   cp completions/clidict.fish ~/.config/fish/completions/
#   # or
#   ln -s (pwd)/completions/clidict.fish ~/.config/fish/completions/

# Disable default file completions
complete -c clidict -f

# Dynamic word completions from bundled dict files.
# Uses --_complete flag, works with pip install and PyInstaller binary.
complete -c clidict -k -a '(clidict --_complete -- (commandline -ct) 2>/dev/null)'
