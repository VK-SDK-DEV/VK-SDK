import threading
from . import events
from . import listExtension


class ThreadManager(object):
    thread_poll = listExtension.ListExtension()
    
    @classmethod
    def get_main_thread(cls):
        return cls.threadByName("Main")

    @classmethod
    def threadByName(cls, name):
        return cls.thread_poll.find(lambda item: item.name == name)

    def changeInterval(self, name, newInterval):
        thread = self.threadByName(name)
        thread.interval = newInterval

    @classmethod
    def create_task(cls, name, task, *args, **kwargs):
        thread = cls.threadByName(name)
        thread.create_task(task, *args, **kwargs)

    def __getitem__(self, key):
        return self.threadByName(key)


class Thread(threading.Thread):
    def __init__(self, *args, **kwargs) -> None:
        ThreadManager.thread_poll.append(self)
        self.tasks = []
        super().__init__(*args, **kwargs)

    def create_task(self, task, *args, **kwargs):
        self.tasks.append((task, args, kwargs))

    def check_tasks(self):
        while len(self.tasks) > 0:
            task = self.tasks.pop(0)
            task[0](*task[1], **task[2])


def requires_start(func):
    def call_wrap(*args, **kwargs):
        if main_thread is None or not getattr(main_thread, "started", False):
            @events.once("start")
            def _():
                func(*args, **kwargs)
        else:
            func(*args, **kwargs)

    return call_wrap


def threaded(*args, **kwargs):
    def func_wrap(func):
        def call_wrap(*a, **b):
            Thread(*args, **kwargs, target=func, args=a, kwargs=b).start()
        return call_wrap
    return func_wrap


class Every(Thread):
    def __init__(self, interval, *args, onExecCallback=None, callback=None, **kwargs):
        if callback is not None:
            self.callback = callback
        elif hasattr(self, "loop"):
            self.callback = self.loop
        else:
            raise Exception("Callback wasn't provided.")
        self.interval = interval
        self.stopped = False
        self.event = threading.Event()
        self.onExecCallback = onExecCallback
        self.args = args
        super().__init__(**kwargs)
        self.start()

    # override
    def run(self):
        """
        The run function runs callback function. It checks for new tasks, and executes them.
        
        :param self: Used to Access the class instance from within the function.
        """
        self.callback(*self.args)
        while not self.event.wait(self.interval) and not self.stopped:
            if self.onExecCallback is not None:
                self.onExecCallback()
            self.check_tasks()
            self.callback(*self.args)


def every(interval, *myArgs, callback=None, **myKwargs):
    """
    The every function is a decorator that schedules the given function to be called periodically. 
    The decorated function is called with the given arguments and keyword arguments, as well as any additional 
    arguments passed when calling the Every instance. The decorated function is called at first invocation 
    and then repeatedly every interval seconds, or with an optional initial delay.
    
    :param interval: Used to Set the time interval between each execution of the function.
    :param *myArgs: Used to Pass arguments to the function that is being called.
    :param callback=None: Used to Pass a function to be called when the timer is executed.
    :param **myKwargs: Used to Pass in keyword arguments to the callback function.
    :return: A function that is a wrapper around the original function.
    """
    def func_wrap(func):
        return Every(interval, *myArgs, onExecCallback=callback, **myKwargs, callback=func)

    return func_wrap

main_thread = None

@events.once("start")
def update_main_thread():
    global main_thread
    main_thread = ThreadManager.threadByName("Main")
