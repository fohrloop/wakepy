r"""This is a simple script for testing wakepy (manually). It is similar to
scripts\example-test.py but there's a wakepy mode activated & deactivated
before the timer starts.

Can be used to determine the status of the system sleep timer right after
exiting the wakepy mode.
"""

import datetime as dt
import time

from wakepy import keep

start = dt.datetime.now()
now = None
MODE_ACTIVE_TIME = 6 * 60  # seconds

print(dt.datetime.now().strftime("%b %d %H:%M:%S"))
print("Wakepy inhibit start")
with keep.presenting() as m:
    print(f"Method: {m.result.method}, " f"Mode: {m.result.mode_name}")
    time.sleep(MODE_ACTIVE_TIME)
    print("Wakepy inhibit end")

while True:
    prev = now or dt.datetime.now()
    now = dt.datetime.now()
    now_str = now.strftime("%b %d %H:%M:%S")
    delta_str = f"{(now-prev)/dt.timedelta(seconds=1)}s"
    print(f"{now_str} | elapsed {now-start} | delta: {delta_str}")
    time.sleep(2)
