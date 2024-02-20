def get_version():
    from importlib import resources
    return resources.files('itask').joinpath('__version__').read_text()
