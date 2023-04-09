class KeepAwakeModuleFunction:
    name: KeepAwakeModuleFunctionName
    is_required: bool = True


functions = [
    KeepAwakeModuleFunction(
        name=KeepAwakeModuleFunctionName.SET_KEEPAWAKE,
        is_required=True,
    ),
    KeepAwakeModuleFunction(
        name=KeepAwakeModuleFunctionName.UNSET_KEEPAWAKE,
        is_required=True,
    ),
]
