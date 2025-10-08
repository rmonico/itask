import os
import yaml


def load():
    global _configs
    _configs = _get_config_defaults()

    config_file = _get_config_file()

    if not os.path.exists(config_file):
        return

    with open(config_file) as file:
        user_configs = yaml.safe_load(file) or {}

    _configs.update(user_configs)


def _get_config_file():
    import os

    config_folder = _get_config_folder()
    return os.path.join(config_folder, 'config.yaml')


def _get_config_folder():
    return os.environ.get('XDG_CONFIG_FOLDER',
                          os.path.join(os.environ['HOME'], '.config', 'itask'))


def _get_config_defaults():
    from importlib import resources
    file = resources.files('itask').joinpath('default_keys.yaml').read_text()

    return yaml.safe_load(file)


def get(key):
    entry = _configs

    for subkey in key.split('.'):
        entry = entry[subkey]

    return entry
