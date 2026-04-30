# Bash tab-completion for camdict
# Install: source this file in ~/.bashrc or copy to /etc/bash_completion.d/
#
#   echo 'source /path/to/completions/camdict.bash' >> ~/.bashrc
#   # or
#   sudo cp completions/camdict.bash /etc/bash_completion.d/

_camdict_complete() {
    local cur prev words cword
    _init_completion || return
    COMPREPLY=($(compgen -W "$(camdict --_complete "$cur" 2>/dev/null)" -- "$cur"))
}

complete -F _camdict_complete camdict
