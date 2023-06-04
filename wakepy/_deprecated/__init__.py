from importlib import import_module

def import_module_for_method(system, method):
    return import_module(f"._{system}._{method}", "wakepy._deprecated")

