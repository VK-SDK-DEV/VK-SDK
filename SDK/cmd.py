# command + after func 
import difflib
from SDK.listExtension import ListExtension
from SDK import database

class AfterFunc(database.Struct):
    def __init__(self, *args, **kwargs):
        self.save_by = database.ProtectedProperty("user_id")
        self.table_name = database.ProtectedProperty("after_func")
        self.user_id = database.Sqlite3Property("", "not null unique")
        self.after_name = ""
        self.database_class = database.ProtectedProperty(None)
        super().__init__(*args, **kwargs)

command_poll = [] # MutableList<Command>
after_func_poll = {} #name to callable map

# data class for commands
class Command(object):
    def __init__(self, name, aliases, fixTypo, callable):
        self.name = name
        self.aliases = aliases
        self.fixTypo = fixTypo
        self.callable = callable

def command(name, fixTypo = True, aliases = ListExtension()):
    def func_wrap(func):
        command_poll.append(Command(name, aliases + name, fixTypo, func))
    return func_wrap

def after_func(name):
    def func_wrap(func):
        after_func_poll[name] = func
    return func_wrap

def set_after(name, uID):
    struct = AfterFunc(database.db, after_name = name, user_id = uID)
    struct.after_name = name

def execute_command(name, botClass):
    selected = database.db.select_one_struct("select * from after_func where user_id = ?", "after_func", [botClass.user.id])
    #prefer names over fixed commands
    if selected is not None and selected.after_name != "null":
        tmpAfterName = selected.after_name
        resetToNull = True
        if tmpAfterName in after_func_poll:
            resetToNull = after_func_poll[tmpAfterName](botClass)
        if resetToNull is None: resetToNull = True
        if resetToNull:
            selected.after_name = "null"
        return
    for cmd in command_poll:
        if cmd.name == name or name in cmd.aliases:
            cmd.callable(botClass, botClass.args)
            return
    for cmd in command_poll:
        if not cmd.fixTypo: continue
        matches = difflib.get_close_matches(name, cmd.aliases, cutoff=0.7)
        if not matches: continue
        cmd.callable(botClass, botClass.args)
        return