# Bash tab-completion for clidict
# Install: source this file in ~/.bashrc or copy to /etc/bash_completion.d/
#
#   echo 'source /path/to/completions/clidict.bash' >> ~/.bashrc
#   # or
#   sudo cp completions/clidict.bash /etc/bash_completion.d/

_clidict_complete() {
    local cur prev words cword
    _init_completion || return
    COMPREPLY=($(compgen -W "$(clidict --_complete "$cur" 2>/dev/null)" -- "$cur"))
}

complete -F _clidict_complete clidict
