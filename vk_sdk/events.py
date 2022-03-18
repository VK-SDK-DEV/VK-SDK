
class Event(object):
    """Custom class for event handling"""
    callbacks = {}

    def __init__(self, name, func, param="") -> None:
        """
        The __init__ function is called when an instance of the class is created. 
        It initializes all of the variables that are defined in the __init__ function, 
        and it sets up any functions that will be used with instances of this class.
        
        :param self: Used to Reference the object itself.
        :param name: Used to Identify the event.
        :param func: Used to Specify the function that should be called when the event is triggered.
        :param param="": Used to define event behaviour (on - don't remove callback after event occurs, once - remove callback)
        :return: None.
        
        :doc-author: Trelent
        """
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
    """
    The on function is a decorator that registers an event handler.
    It takes the name of the event as its first argument, and a function as its second argument.
    The decorated function will be called whenever the named event is triggered.
    
    :param name: Used to Identify the event.
    :return: A function that takes a function as an argument.
    """
    def func_wrap(func):
        Event(name, func, "on")
    return func_wrap

def once(name):
    """
    The once function is a decorator that will only call the decorated function once. 
    The decorated function will be called whenever the named event is triggered and then callback will be removed.
    
    :param name: Used to Identify the event.
    :return: A function that takes a function as an argument.
    
    :doc-author: Trelent
    """
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
