from wakepy import keep, modecount


@keep.running
def long_running_function():
    assert modecount() == 1


long_running_function()
