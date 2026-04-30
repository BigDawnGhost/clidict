# Fish tab-completion for camdict
# Install: copy or symlink to ~/.config/fish/completions/camdict.fish
#
#   cp completions/camdict.fish ~/.config/fish/completions/
#   # or
#   ln -s (pwd)/completions/camdict.fish ~/.config/fish/completions/

# Disable default file completions
complete -c camdict -f

# Dynamic word completions from /usr/share/dict
# Uses --_complete flag, works with pip install and PyInstaller binary
complete -c camdict -a '(camdict --_complete -- (commandline -ct) 2>/dev/null)'
