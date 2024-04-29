# vim: filetype=sh

project_dir="$(realpath "$(dirname "$0")")"
this_script="$(realpath "$0")"
virtualenv_name="itask"

# version="0.3.11"
# python_user_install_dirs=["$HOME/.local/lib/python3.11/site-packages/itask", f"$HOME/.local/lib/python3.11/site-packages/iTask-{version}.dist-info"]
# python_binary="$HOME/.local/bin/itask"


_variables=(
    project_dir
    this_script
    virtualenv_name
)

_functions=()

_functions+=run
function run() {
    cd "$project_dir"

    python -m itask

    cd - &> /dev/null
}

_functions+=install_local
function install_local() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "VirtualEnv enabled. Cant install locally"
        return 1
    fi

    cd "$project_dir"

    python -m pip install --user --break-system-packages .

    cd - &> /dev/null
}

_functions+=reload
function reload() {
    cd "$project_dir"

    _reloading=yes

    local _this_script="$this_script"

    off

    source "$_this_script"

    unset _reloading

    echo Ambiente recarregado

    cd - &> /dev/null
}

function _initialize() {
    [ "$_reloading" != "yes" ] && {
        _do_initialize
    }

    unset -f _initialize _do_initialize
}

function _do_initialize() {
    source virtualenvwrapper.sh && workon "$virtualenv_name"

    echo Ambiente ativado
}

_functions+=off
function off() {
    unset ${_variables[@]}
    unset -f ${_functions[@]}

    [ "$_reloading" != "yes" ] && {
        deactivate

        echo Ambiente desativado
    }
}

_initialize
