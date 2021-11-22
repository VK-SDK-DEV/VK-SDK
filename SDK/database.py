import os
import re
import sqlite3
from collections import namedtuple
from typing import AnyStr, Any, Iterable
from sqlite3 import Row

from SDK import jsonExtension, thread, timeExtension
from SDK.listExtension import ListExtension


def getter(x: Any, attr: AnyStr): return getattr(x, attr, x)


def attrgetter(x: Any): return getter(x, "value")


def formAndExpr(baseSql, argsList, getattrFrom, add):
    for i, k in enumerate(add):
        baseSql += f"{k}=?"
        argsList.append(getattr(getattrFrom, k))
        if i != len(add) - 1:
            baseSql += " and "
    return baseSql, argsList


def to_sneak_case(string):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()


# Handle all stuff behind Struct instances
def convert_to_list_if_needed(element):
    if not isinstance(element, list):
        return ListExtension([element])
    else:
        return ListExtension(element)


class Struct(object):
    table_map = {}

    @classmethod
    def extract_table_name(cls):
        if hasattr(cls, "table_name"):
            return getattr(cls, "table_name")
        else:
            return to_sneak_case(cls.__name__)

    @classmethod
    def extract_save_by(cls):
        if hasattr(cls, "save_by"):
            return convert_to_list_if_needed(attrgetter(cls.save_by))
        for k, v in vars(cls).items():
            if isinstance(v, Sqlite3Property) and "unique" in v.type:
                return ListExtension(k)

    def __init_subclass__(cls) -> None:
        cls.table_name = cls.extract_table_name()
        cls.save_by = cls.extract_save_by()
        cls.table_map[cls.table_name] = cls
        return super().__init_subclass__()

    def __init__(self, **kwargs) -> None:
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
            if db is not None and self.save_by.all(lambda it: it in kwargs.keys()):
                expr = f"select * from {self.table_name} where "
                args = []
                n = namedtuple('Struct', kwargs.keys())(**kwargs)
                expr, args = formAndExpr(expr, args, n, self.save_by)
                old_struct = db.select_one_struct(expr, args)
                if old_struct is None:
                    keys, values = ListExtension(), ListExtension()
                    vrs = self.vars()
                    for key, value in vrs.items():
                        keys.append(key)
                        values.append(kwargs[key]) if kwargs.get(key) is not None else values.append(value)
                    insert_string = f"insert or ignore into {self.table_name} ({','.join(keys)}) values ({values.map(lambda _: '?', copy=True).join(',')})"
                    db.execute(insert_string, values)
                    variables = self.vars()
                    self.fill(variables.keys(), variables)
                else:
                    keys = kwargs.keys()
                    values = ListExtension(kwargs.values()).filter(
                        lambda it: it not in self.save_by)
                    d = dict(zip(keys, values))
                    for k, v in d.items():
                        old_struct.setattr(k, v)
                    variables = old_struct.vars()
                    self.fill(variables.keys(), variables)
                self.initialized = True

        super().__init__()


    def boundStructByAction(self, key, data):
        data = getattr(data, "dictionary", data)
        structByAction = jsonExtension.StructByAction(data)
        structByAction.action = lambda _: db.save_struct_by_action(
            self.table_name, key, structByAction, self.save_by, self)
        return structByAction

    def destroy(self):
        lst = []
        sql = f"delete from {self.table_name} where "
        sql, lst = formAndExpr(sql, lst, self, self.save_by)
        db.execute(sql, lst)

    def setattr(self, key, value, write_to_database=True):
        prev = getattr(self, key, None)
        if prev == value:
            return
        if write_to_database and getattr(self, "initialized", False):
            if isinstance(prev, jsonExtension.StructByAction):
                super().__setattr__(key, self.boundStructByAction(key, value))
                getattr(self, key).action(None)
            else:
                db.write_struct(self, key, value)
                super().__setattr__(key, value)
        else:
            super().__setattr__(key, value)

    def vars(cls):
        attrs = {k: getattr(cls, k) for k in dir(cls)}
        return {k: v for k, v in attrs.items() if not k.startswith(
                "__") and k not in ["table_name", "save_by", "initialized", "table_map"] and not callable(v)}

    def fill(self, keys, getitemfrom):
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

    def __init__(self, file: AnyStr, backup_folder: AnyStr, bot_class, **kwargs):
        self.backup_folder = backup_folder
        folder = os.path.split(file)[0]
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.file = file
        self.bot_class = bot_class
        self.db = sqlite3.connect(file, check_same_thread=False, **kwargs)
        self.row_factory = sqlite3.Row
        self.db.row_factory = self.row_factory
        self.cursor = self.db.cursor()

        for struct in Struct.table_map.values():
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

        thread.every(self.bot_class.config["db_backup_interval"], name="Backup")(
            self.backup)

    def backup(self):
        if not self.bot_class.config["db_backups"]:
            return

        rawName = self.file.split("/")[-1]
        manager = thread.ThreadManager()
        manager.changeInterval(
            "Backup", self.bot_class.config["db_backup_interval"])
        backup_table = sqlite3.connect(
            f"{self.backup_folder}backup_{timeExtension.now()}_{rawName}")
        self.db.backup(backup_table)

    def select(self, query: AnyStr, args=None):
        if args is None:
            args = []
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def create_execute_task(self, query, args=None):
        if args is None:
            args = []
        thread.ThreadManager.get_main_thread().create_task(db.execute, query, args)

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

    def select_all_structs(self, query: AnyStr, *args):
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
