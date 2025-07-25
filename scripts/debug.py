from wakepy import keep, modecount


@keep.running(methods=["MethodForThreadSafety"])
def long_running_function():
    assert modecount() == 1


long_running_function()
