"""This is a simple script for testing wakepy (manually)
"""

import datetime as dt
import time

start = dt.datetime.now()
now = None
while True:
    prev = now or dt.datetime.now()
    now = dt.datetime.now()
    now_str = now.strftime("%b %d %H:%M:%S")
    delta_str = f"{(now-prev)/dt.timedelta(seconds=1)}s"
    print(f"{now_str} | elapsed {now-start} | delta: {delta_str}")
    time.sleep(2)
