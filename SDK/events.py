
class Event(object):
    callbacks = {}

    def __init__(self, name, func, param="") -> None:
        self.name = name
        self.param = param
        self.func = func
        callbacks = self.callbacks.get(name)
        if callbacks is None:
            Event.callbacks[name] = [self]
        else:
            Event.callbacks[name].append(self)
        super().__init__()

def on(name):
    def func_wrap(func):
        Event(name, func, "on")
    return func_wrap

def once(name):
    def func_wrap(func):
        Event(name, func, "once")
    return func_wrap


def emit(name, *args, **kwargs):
    callbacks = Event.callbacks.get(name)
    if callbacks is not None:
        for iterable, callback in enumerate(callbacks):
            callback.func(*args, **kwargs)
            if callback.param == "once":
                del Event.callbacks[name][iterable]
