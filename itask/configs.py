import os
import yaml


def load():
    config_file = _get_config_file()

    global _configs
    if not os.path.exists(config_file):
        _configs = {}
    else:
        with open(config_file) as file:
            _configs = yaml.safe_load(file) or {}

    _add_config_defaults()


def _get_config_file():
    import os

    config_folder = _get_config_folder()
    return os.path.join(config_folder, 'config.yaml')


def _get_config_folder():
    return os.environ.get('XDG_CONFIG_FOLDER', os.path.join(os.environ['HOME'], '.config', 'itask'))


def _add_config_defaults():
    from importlib import resources
    file = resources.files('itask').joinpath('default_keys.yaml').read_text()

    defaults = yaml.safe_load(file)

    global _configs
    _configs.update(defaults)


def get(key):
    entry = _configs

    for subkey in key.split('.'):
        entry = entry[subkey]

    return entry
