"""Module for managing commands"""


# command + after func
import difflib
from functools import partial
import inspect
from types import NoneType

from vk_sdk.listExtension import ListExtension

from . import user
from . import database
from .jsonExtension import StructByAction


class AfterFunc(database.Struct):
    """Structure for AfterFuncs"""
    save_by = "user_id"
    user_id = database.Sqlite3Property("", "not null unique")
    after_name = ""
    args = []


class Panels(database.Struct):
    save_by = "user_id"
    user_id = database.Sqlite3Property("", "not null unique")
    panel_name = ""


class AbstractAfterFunc(object):
    def __new__(cls, name, func=None, circular=None):
        if (instance := after_func_poll.get(name)) is None:
            return super().__new__(cls)
        return instance

    def __init__(self, name, func=None, circular=None) -> None:
        if getattr(self, "circular", None) is None and circular is not None:
            self.circular = circular
        if after_func_poll.get(name) is None:
            self.name = name
            self.text_matchers = {}
            after_func_poll[name] = self
        if func is not None:
            self.text_matchers["default"] = func


command_poll = []  # MutableList<Command>
after_func_poll = {}


class CircularBuilder(object):
    def __init__(self, panels_return=None) -> None:
        if panels_return is None:
            panels_return = []
        self.panels_return = PanelsReturn(panels_return, self)
        self.invalid_handlers = {}

    def register_invalid_handler(self, name="default"):
        def func_wrap(func):
            self.invalid_handlers[name] = func
            return self
        return func_wrap

    def invalid_handler(self, botClass, name="default"):
        (get := self.invalid_handlers.get(name)) and get(botClass)


class PanelsReturn(list):
    def __new__(cls, other, parentClass):
        if isinstance(cls, PanelsReturn):
            return cls
        return super().__new__(cls)

    def __init__(self, other, parentClass):
        super().__init__(other)
        self.parentClass = parentClass

    def extend(self, other) -> CircularBuilder:
        if isinstance(other, str):
            super().append(other)
        else:
            super().extend(other)
        return self.parentClass


def _default_allow_enter(*args): return True


class Panel(object):

    panels = ListExtension()

    def __new__(cls, name, aliases=None, circular=None):
        if (panel := cls.find_panel(name)) is not None:
            return panel
        return super().__new__(cls)

    def get_all_names(self):
        return [self.name] + self.aliases

    @classmethod
    def find_panel(cls, name):
        return cls.panels.find(lambda it: name in it.get_all_names())

    def __init__(self, name, aliases=None, circular: CircularBuilder or NoneType = None) -> None:
        if aliases is None:
            aliases = []
        self.name = name
        self.aliases = aliases
        self.circular = circular or CircularBuilder()
        self.panels.append(self)
        self.command_poll = []
        self.allow_enter_func = _default_allow_enter

    def enter(self):
        def func_wrap(func):
            self.enter_func = func
        return func_wrap

    def run(self, botClass):
        Panels(user_id=botClass.user.id).panel_name = self.name

        return call_command(self.enter_func, botClass, botClass.args)

    def check(self, botClass):
        return self.allow_enter_func(botClass)

    def allow_enter(self):
        def func_wrap(func):
            self.allow_enter_func = func
        return func_wrap

    def check_and_run(self, botClass):
        if self.check(botClass):
            return self.run(botClass)

    def command(self, name, aliases=None, fixTypo=False):
        if aliases is None:
            aliases = []

        def func_wrap(func):
            self.command_poll.append(Command(name, aliases, fixTypo, func))
        return func_wrap

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


menu = Panel("меню", aliases=["start", "бот", "старт", "начать"])


def after_func_from_lambda(name, func):
    """Generates a after function from lambda

    Args:
        name (str): name of after function
        func (function): lambda function to generate after_func from
    """
    after_func(name)(func)


def after_func(name, circular=None):
    """
    The after_func function is a decorator that takes the name of after function as an argument. 

    :param name: Used to identify after function.
    :return: A function object which is assigned to func_wrap.
    """
    def func_wrap(func):
        AbstractAfterFunc(name, func, circular)
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
        name (str): Name of after function.
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


def emulate_command(botClass, command, user_id=None, after_func=None, after_ags=None):
    if user_id is not None:
        botClass.user = user.User(user_id)
        if after_func is not None:
            set_after(after_func, user_id, after_ags)
    botClass.init_text(command)
    execute_command(botClass)


def execute_command(botClass):
    selected = AfterFunc(create_new=False, user_id=botClass.user.id)
    selected_panel = Panels(create_new=False, user_id=botClass.user.id)
    _p = None
    if selected_panel is not None:
        _p = Panel.find_panel(selected_panel.panel_name)
        command_poll = _p.command_poll
    else:
        command_poll = globals()["command_poll"]

    if selected is not None and selected.after_name != "null":
        tmpAfterName = selected.after_name
        selected.after_name = "null"
        doNotReset = False
        if tmpAfterName in after_func_poll:
            after_func: AbstractAfterFunc = after_func_poll[tmpAfterName]
            if getattr(after_func, "circular", None) is not None:
                for panel in after_func.circular.panels_return:
                    _p: Panel = Panel.find_panel(panel)
                    if not _p:
                        continue
                    if botClass.text in _p.get_all_names() and _p.check(botClass):
                        _p.run(botClass)
                        return

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
    if not _p:
        _p = Panel.find_panel(botClass.text)
        if _p and _p.check(botClass):
            _p.run(botClass)
            return
    prepared = None
    for i in botClass.txtSplit:
        tmpCmd.append(i)
        name = " ".join(tmpCmd)
        # prefer names over fixed commands
        for cmd in command_poll:
            if cmd.name == name or name in cmd.aliases:
                prepared = partial(call_command, cmd.callable,
                                   botClass, botClass.args)
                break
        for cmd in command_poll:
            if not cmd.fixTypo:
                continue
            matches = difflib.get_close_matches(name, cmd.aliases, cutoff=0.7)
            if not matches:
                continue
            prepared = partial(call_command, cmd.callable,
                               botClass, botClass.args)
            break

    if prepared is not None:
        prepared()
        return

    if _p is not None:
        for ret in _p.circular.panels_return:
            __p: Panel = Panel.find_panel(ret)
            if not __p:
                continue
            if botClass.text in __p.get_all_names() and __p.check(botClass):
                __p.run(botClass)
                break
        else:
            _p.circular.invalid_handler(botClass)
