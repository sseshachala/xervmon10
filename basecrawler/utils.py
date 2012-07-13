from functools import wraps
import time
from pymongo.errors import AutoReconnect

def reconnect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 2
        num_fails = 0
        while 1:
            try:
                return func(*args, **kwargs)
            except AutoReconnect, e:
                num_fails += 1
                time.sleep(0.1)
                if num_fails >= max_retries:
                    raise e
    return wrapper
