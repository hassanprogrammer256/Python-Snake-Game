import threading
from typing import Callable


def set_interval(func: Callable, seconds: int, args=[], kwargs={}):

    def func_wrapper():
        set_interval(func, seconds, args, kwargs)
        func(*args, **kwargs)
    t = threading.Timer(seconds, func_wrapper)
    t.start()
