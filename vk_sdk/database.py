import os
import re
import sqlite3
from collections import namedtuple
from typing import AnyStr, Any, Iterable
from sqlite3 import Row

from . import jsonExtension, thread, timeExtension
from .listExtension import ListExtension


def getter(x: Any, attr: AnyStr): return getattr(x, attr, x)


DEFAULT_CONFIG = """
{
    "db_file": "data/db.sqlite3",
    "db_backups": false,
    "db_backups_folder": "backups/",
    "db_backup_interval": 43200,
    "sync_timezone": "Europe/Moscow",
    "vk_api_key": ""
}
"""

config = jsonExtension.loadAdvanced("config.json", content=DEFAULT_CONFIG)


def attrgetter(x: Any): return getter(x, "value")


def formAndExpr(baseSql, argsList, getattrFrom, add):
    """
    The formAndExpr function takes a baseSql string, an argsList list, and a getattrFrom object. It then adds the attributes from the add list to the baseSql string and appends their values to argsList.
    
    :param baseSql: Used to Store the sql query that will be used to update the database.
    :param argsList: Used to Store the values of the parameters in add.
    :param getattrFrom: Used to Get the values from the object.
    :param add: Used to Add the column names to the basesql string.
    :return: A string that is a concatenation of the strings in add, each followed by an "and" and surrounded by open and close parentheses.
    """
    for i, k in enumerate(add):
        baseSql += f"{k}=?"
        argsList.append(getattr(getattrFrom, k))
        if i != len(add) - 1:
            baseSql += " and "
    return baseSql, argsList


def to_sneak_case(string):
    """
    The to_sneak_case function converts a string to snake_case.
    
    Args:
        string (str): The input string. 
    Returns:
        str: The output snake_case formatted string.
    
    :param string: Used to Define the string that will be converted to sneak case.
    :return: A string in sneak case.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()


# Handle all stuff behind Struct instances
def convert_to_list_if_needed(element):
    """
    The convert_to_list_if_needed function checks if the input is a list. If it is not, it converts the input to a list and returns that. Otherwise, it just returns the original element.
    
    :param element: Used to Check if the element is a list.
    :return: A listextension object.
    """
    if not isinstance(element, list):
        return ListExtension([element])
    else:
        return ListExtension(element)


class Struct(object):
    table_map = {}

    @classmethod
    def extract_table_name(cls):
        """Searches for table_name in Struct"""
        if hasattr(cls, "table_name"):
            return getattr(cls, "table_name")
        else:
            return to_sneak_case(cls.__name__)

    @classmethod
    def extract_save_by(cls):
        """
        The extract_save_by function is used to extract the save_by attribute from a class.
        
        If the class has no save_by attribute, it will look for any attributes that are instances of Sqlite3Properties and return them in a list.
        
        :param cls: Used to Access the class object of the current instance.
        :return: A list of the names of all the attributes that are marked for saving.
        """
        if hasattr(cls, "save_by"):
            return convert_to_list_if_needed(attrgetter(cls.save_by))
        for k, v in vars(cls).items():
            if isinstance(v, Sqlite3Property) and "unique" in v.type:
                return ListExtension(k)

    def __init_subclass__(cls) -> None:
        """
        The __init_subclass__ function is called when some class derives from our Struct
        It’s purpose is to ensure that all subclasses of the base class have their own table_name and save_by attributes, 
        and that they are kept in sync with the base class via an updated table_map.
        
        :param cls: Used to Access the class object.
        :return: The class object that is being defined.
        """
        cls.table_name = cls.extract_table_name()
        cls.save_by = cls.extract_save_by()
        cls.table_map[cls.table_name] = cls
        return super().__init_subclass__()

    def define_db(self):
        if hasattr(self, "use_db"):
            self.db = Database.db_cache[self.use_db]
        else:
            self.db = db

    def __new__(cls, **kwargs):
        create_new = kwargs.get("create_new", True)
        cls.define_db(cls)
        instance = super().__new__(cls)
        instance.setattr("old_struct", None, ignore_duplicates=False)
        if kwargs:
            expr = f"select * from {cls.table_name} where "
            args = []
            n = namedtuple('Struct', kwargs.keys())(**kwargs)
            expr, args = formAndExpr(expr, args, n, cls.save_by)
            old_struct = cls.db.select_one_struct(expr, args)
            if old_struct is None and create_new is False:
                return None
            instance.old_struct = old_struct
        return instance

    def __init__(self, create_new=None, **kwargs) -> None:
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
            if self.save_by.all(lambda it: it in kwargs.keys()):
                if self.old_struct is None:
                    keys, values = ListExtension(), ListExtension()
                    vrs = self.vars()
                    for key, value in vrs.items():
                        keys.append(key)
                        values.append(kwargs[key]) if kwargs.get(
                            key) is not None else values.append(value)
                    insert_string = f"insert or ignore into {self.table_name} ({','.join(keys)}) values ({values.map(lambda _: '?', copy=True).join(',')})"
                    self.db.execute(insert_string, values)
                    variables = self.vars()
                    self.fill(variables.keys(), variables)
                else:
                    keys = kwargs.keys()
                    values = ListExtension(kwargs.values()).filter(
                        lambda it: it not in self.save_by)
                    d = dict(zip(keys, values))
                    for k, v in d.items():
                        self.old_struct.setattr(k, v)
                    variables = self.old_struct.vars()
                    self.fill(variables.keys(), variables)
                self.initialized = True

        super().__init__()

    def boundStructByAction(self, key, data):
        """Bounds struct by action to a given data (list or dict). Struct by action will handle the watching on elements change."""
        data = getattr(data, "dictionary", data)
        structByAction = jsonExtension.StructByAction(data)
        structByAction.action = lambda _: self.db.save_struct_by_action(
            self.table_name, key, structByAction, self.save_by, self)
        return structByAction

    def destroy(self):
        """
        The destroy function deletes Struct record from db.
        
        :param self: Used to Refer to the object itself.
        """
        lst = []
        sql = f"delete from {self.table_name} where "
        sql, lst = formAndExpr(sql, lst, self, self.save_by)
        self.db.execute(sql, lst)

    def setattr(self, key, value, write_to_database=True, ignore_duplicates=True):
        """
        The setattr function is a helper function that allows us to write the value of an attribute to the database.
        It is called when we set an attribute on a Struct, and it will only write to the database if:
        - The struct has been initialized (i.e., it's ready to use and that's not some internal module call)
        - The key being assigned matches one of our attributes (otherwise, we might be trying to assign something that doesn't correspond with any known field in our struct)
        - The value being assigned is different from what was previously stored for this key in our struct (unless ignore_duplicates=True). This prevents us from writing unnecessary updates.
        Otherwise it's some internal package calls.

        :param self: Used to Reference the object that is calling the function.
        :param key: Used to Specify the attribute that is to be set.
        :param value: Used to Set the value of an attribute.
        :param write_to_database=True: Do we need to write changed value to db.
        :param ignore_duplicates=True: Used to Avoid writing the same value to the database multiple times.
        :return: None.
        """
        prev = getattr(self, key, None)
        if prev == value and ignore_duplicates:
            return
        if write_to_database and getattr(self, "initialized", False):
            if isinstance(prev, jsonExtension.StructByAction):
                super().__setattr__(key, self.boundStructByAction(key, value))
                getattr(self, key).action(None)
            else:
                self.db.write_struct(self, key, value)
                super().__setattr__(key, value)
        else:
            super().__setattr__(key, value)

    def vars(cls):
        """
        The vars function is used to extract the class variables from a class.
        
        :param cls: Used to Indicate the class that we want to get attributes from.
        :return: A dictionary of the class's namespace.
        """
        attrs = {k: getattr(cls, k) for k in dir(cls)}
        return {k: v for k, v in attrs.items() if not k.startswith(
                "__") and k not in ["table_name", "save_by", "initialized", "table_map", "use_db", "db", "old_struct"] and not callable(v)}

    def fill(self, keys, getitemfrom):
        """Fills attributes mapped from list[str] keys to getitemfrom object to our Struct"""
        for k in keys:
            v = getitemfrom[k]
            attr = v
            data, value = jsonExtension.isDeserializable(v)
            if isinstance(v, list) or isinstance(v, dict):
                attr = self.boundStructByAction(k, v)
            elif value:
                attr = self.boundStructByAction(k, data)
            if isinstance(getattr(self, k), bool):
                attr = self.str2bool(attr)
            self.setattr(k, attr, False)

    def __setattr__(self, name: str, value: Any) -> None:
        self.setattr(name, value)

    def str2bool(self, v):
        if hasattr(v, "lower"):
            return v.lower() in ("true", "1")
        else:
            return v


class Sqlite3Property(object):
    def __init__(self, x: Any, y: AnyStr):
        self.value = x
        self.type = y


class Database(object):

    typeToTypeCache = {str: "text", dict: "str", list: "str",
                       float: "real", type(None): "null", int: "int", bool: "bool"}
    db_cache = {}

    def __new__(cls, settings, **kwargs):
        file = settings["db_file"]
        if (instance := cls.db_cache.get(file)) is None:
            instance = super().__new__(cls)
            cls.db_cache[os.path.basename(
                os.path.splitext(file)[0])] = instance  # short path
            cls.db_cache[file] = instance
            return instance
        return instance

    def __init__(self, settings: dict, **kwargs):
        self.settings = settings
        self.backup_folder = self.settings["db_backups_folder"]
        folder = os.path.split(self.settings["db_file"])[0]

        if not os.path.exists(folder):
            os.makedirs(folder)
        self.file = self.settings["db_file"]
        self.db = sqlite3.connect(
            self.settings["db_file"], check_same_thread=False, **kwargs)
        self.row_factory = sqlite3.Row
        self.db.row_factory = self.row_factory
        self.cursor = self.db.cursor()

        is_main_table = self.settings["db_file"] == config["db_file"]

        for struct in Struct.table_map.values():
            if not is_main_table and not hasattr(struct, "use_db") or hasattr(struct, "use_db") and self.db_cache[struct.use_db] != self:
                return
            iterable = -1
            rows = []
            variables = struct.vars(struct)
            for key, value in variables.items():
                iterable += 1
                real_value = attrgetter(value)
                rows.append(
                    f"{key} {self.convert_type(real_value)} {getattr(value, 'type', '')} default \"{real_value}\"")
            self.execute(
                f"create table if not exists {struct.table_name} ({', '.join(rows)})")
            table_fields = self.get_column_names(struct.table_name)
            for iterable, field in enumerate(variables.keys()):
                if field not in table_fields:
                    self.execute(
                        f"alter table {struct.table_name} add column {rows[iterable]}")
            for field in list(table_fields):
                if field not in variables:
                    self.execute(
                        f"alter table {struct.table_name} drop column {field}")
        if self.settings["db_backups"]:
            thread.every(self.settings["db_backup_interval"], name="Backup")(
                self.backup)

        global db
        if config["db_file"] == self.settings["db_file"]:
            db = self

    def backup(self):
        if not self.settings["db_backups"]:
            return

        rawName = self.file.split("/")[-1]
        manager = thread.ThreadManager()
        manager.changeInterval(
            "Backup", self.settings["db_backup_interval"])
        backup_table = sqlite3.connect(
            f"{self.backup_folder}backup_{timeExtension.now()}_{rawName}")
        self.db.backup(backup_table)

    def select(self, query: AnyStr, args=None):
        if args is None:
            args = []
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def select_one(self, query: AnyStr, *args):
        if isinstance(args, list):
            self.cursor.execute(query, [str(x) for x in args])
        else:
            self.cursor.execute(query, *args)
        return self.cursor.fetchone()

    def write_struct(self, structToWrite: Struct, changedKey: AnyStr, newValue: Any):
        table = structToWrite.table_name
        unique_fields = Struct.table_map[table].save_by
        sql = f"update or ignore {table} set {changedKey} = ? where "
        argsList = [newValue]
        sql, argsList = formAndExpr(
            sql, argsList, structToWrite, unique_fields)
        self.execute(sql, argsList)

    def select_one_struct(self, query: AnyStr, *args: tuple or jsonExtension.StructByAction,
                          selectedStruct: Row = None,
                          fromSerialized=None, table_name=None):
        table_name = self.parse_table_name(query, table_name)
        struct = self.select_one(
            query, *args) if selectedStruct is None else selectedStruct
        if struct is None:
            return None
        if isinstance(args, jsonExtension.StructByAction):
            args = args.dictionary
        if not isinstance(table_name, str):
            raise Exception(
                f"Table name's type is not string (table_name was not provided correctly?)\n{query=}\n{args=}\n{table_name=}")
        myStruct: Struct = Struct.table_map[table_name](
        ) if fromSerialized is None else fromSerialized
        if struct is None:
            return None
        myStruct.fill(struct.keys(), struct)
        myStruct.setattr("initialized", True, write_to_database=False)
        return myStruct

    def select_all_structs(self, query: AnyStr, *args) -> ListExtension:
        structs = ListExtension.byList(self.select(query, *args))
        return ListExtension.byList([self.select_one_struct(query, *args, selectedStruct=x) for x in structs])

    def save_struct_by_action(self, table_name: AnyStr, key: Any, value: Any,
                              unique_field: Iterable, parent_struct: Struct):
        baseSql = f"update {table_name} set {key} = ? where "
        argsList = [jsonExtension.json.dumps(value.dictionary)]
        baseSql, argsList = formAndExpr(
            baseSql, argsList, parent_struct, unique_field)
        self.execute(baseSql, argsList)

    def execute(self, query: AnyStr, args=None):
        if args is None:
            args = []
        for i, k in enumerate(args):
            if type(k) is dict or type(k) is list:
                args[i] = jsonExtension.json.dumps(k)
            elif type(k) is jsonExtension.StructByAction:
                args[i] = jsonExtension.json.dumps(k.dictionary)
        self.cursor.execute(query, args)
        self.db.commit()
        return self.cursor

    def get_column_names(self, table: AnyStr):
        select = self.cursor.execute(f"select * from {table}")
        return [x[0] for x in select.description]

    def parse_table_name(self, query, fromCached=None):
        if fromCached is None:
            return list(tables_in_query(query))[0]
        return fromCached

    def get_table_names(self):
        return [x["name"] for x in self.select("SELECT name FROM sqlite_master WHERE type='table'")]

    @staticmethod
    def convert_type(value):
        return Database.typeToTypeCache[type(value)]


db: Database = None


# https://grisha.org/blog/2016/11/14/table-names-from-sql/
def tables_in_query(sql_str):
    q = re.sub(r"/\*[^*]*\*+(?:[^*/][^*]*\*+)*/", "", sql_str)
    lines = [line for line in q.splitlines(
    ) if not re.match(r"^\s*(--|#)", line)]
    q = " ".join([re.split(r"--|#", line)[0] for line in lines])
    tokens = re.split(r"[\s)(;]+", q)
    result = set()
    get_next = False
    for tok in tokens:
        if get_next:
            if tok.lower() not in ["", "select"]:
                result.add(tok)
            get_next = False
        get_next = tok.lower() in ["from", "join"]

    return result
