# command + after func
import difflib
import inspect

from . import database
from .jsonExtension import StructByAction


class AfterFunc(database.Struct):
    """Structure for AfterFuncs"""
    save_by = "user_id"
    user_id = database.Sqlite3Property("", "not null unique")
    after_name = ""
    args = []


class AbstractAfterFunc(object):
    def __new__(cls, name, func=None):
        if (instance := after_func_poll.get(name)) is None:
            return super().__new__(cls)
        return instance

    def __init__(self, name, func=None) -> None:
        if after_func_poll.get(name) is None:
            self.name = name
            self.text_matchers = {}
            after_func_poll[name] = self
        if func is not None:
            self.text_matchers["default"] = func


command_poll = []  # MutableList<Command>
after_func_poll = {}


# data class for commands
class Command(object):
    def __init__(self, name, aliases, fixTypo, callableItem):
        self.name = name
        self.aliases = aliases
        self.fixTypo = fixTypo
        self.callable = callableItem


def wait(name, uID, function):
    after_func(name)(function)
    set_after(name, uID)


def command(name, fixTypo=True, aliases=None):
    if aliases is None:
        aliases = []

    def func_wrap(func):
        command_poll.append(Command(name, aliases, fixTypo, func))

    return func_wrap


start_command = command("начать", aliases=["start", "меню", "бот", "старт"])


def after_func_from_lambda(name, func):
    """Generates a after function from lambda

    Args:
        name (str): name of after function
        func (function): lambda function to generate after_func from
    """
    after_func(name)(func)


def after_func(name):
    """
    The after_func function is a decorator that takes the name of after function as an argument. 
    
    :param name: Used to identify after function.
    :return: A function object which is assigned to func_wrap.
    """
    def func_wrap(func):
        AbstractAfterFunc(name, func)
    return func_wrap


def after_text_matcher(name, text):
    """
    The after_text_matcher function is a decorator that can be used to mark functions as 
    the handler for some text. The decorated function should take two arguments, the name of 
    the matcher and the text that matched. For example:
    
        @after_text_matcher('foo', 'bar')
        def handle_foo(self):
            print("I'm after function 'foo' that was executed on text match 'bar'")
    
        # This will cause handle_foo to be called if "bar" was the text of message and after func was set to "foo"
    
    :param name: Used to Identify the function.
    :param text: Used to Store the text that is to be matched.
    :return: Wrapper around function.
    """
    def func_wrap(func):
        function = AbstractAfterFunc(name)
        function.text_matchers[text] = func
    return func_wrap


def set_after(name, uID, args=None):
    """Binds after function to specific user

    Args:
        name (_type_): Name of after function.
        uID (str): user id.
        args (list[Any], optional): Args to be passed when after function will be executed. Defaults to None.
    """
    if args is None:
        args = []
    struct = AfterFunc(after_name=name, user_id=uID)
    struct.after_name = name
    struct.args = args


def call_command(function, *args):
    function_args = inspect.getfullargspec(function).args
    if len(function_args) == 1:
        return function(args[0])
    function(*args)


def execute_command(botClass):
    selected = database.db.select_one_struct("select * from after_func where user_id = ?",
                                             [botClass.user.id])

    if selected is not None and selected.after_name != "null":
        tmpAfterName = selected.after_name
        selected.after_name = "null"
        doNotReset = False
        if tmpAfterName in after_func_poll:
            after_func = after_func_poll[tmpAfterName]
            call = after_func.text_matchers.get(
                botClass.text) or after_func.text_matchers.get("default")
            if call is not None:
                doNotReset = call(botClass) if (isinstance(selected.args,
                                                           StructByAction) and not selected.args.dictionary) or not selected.args else \
                    call(botClass, selected.args)
                if doNotReset is None or call.__name__ == "<lambda>" or not isinstance(doNotReset, bool):
                    doNotReset = False
                if doNotReset:
                    selected.after_name = tmpAfterName
        return
    tmpCmd = []
    # loop over arguments
    for i in botClass.txtSplit:
        tmpCmd.append(i)
        name = " ".join(tmpCmd)
        # prefer names over fixed commands
        for cmd in command_poll:
            if cmd.name == name or name in cmd.aliases:
                call_command(cmd.callable, botClass, botClass.args)
                return
        for cmd in command_poll:
            if not cmd.fixTypo:
                continue
            matches = difflib.get_close_matches(name, cmd.aliases, cutoff=0.7)
            if not matches:
                continue
            call_command(cmd.callable, botClass, botClass.args)
            return
