from wakepy import keep

with keep.running():
    print("This code is running in the keep.running mode.")

print("This code is outside of the keep.running mode.")


@keep.running
def long_running_function():
    print("This function is running in the keep.running mode (long_running_function)")


long_running_function()


print("This code is outside of the long_running_function.")
