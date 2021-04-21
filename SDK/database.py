import sqlite3
import typing
import re
from moz_sql_parser import parse
from functools import partial

from SDK import (thread, timeExtension, jsonExtension)
from SDK.listExtension import ListExtension


def getter(x: typing.Any, attr: typing.AnyStr): return getattr(x, attr) if hasattr(x, attr) else x


def adv_getter(x: typing.Any, attr: typing.AnyStr, default: typing.Any): return getattr(x, attr) if hasattr(x,
                                                                                                            attr) \
    else default


def attrgetter(x: typing.Any): return getter(x, "value")


def formAndExpr(baseSql, argsList, getattrFrom, add):
    if type(add) is list:
        for i, k in enumerate(add):
            baseSql += f"{k}=?"
            argsList.append(getattr(getattrFrom, k))
            if i != len(add) - 1:
                baseSql += " and "
    else:
        argsList.append(getattr(getattrFrom, add))
        baseSql += f"{add}=?"
    return baseSql, argsList

def to_sneak_case(string):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()

# Handle all stuff behind Struct instances
class Struct(object):
    table_map = {}
    class_poll = ListExtension([])
    must_implement = []

    def __init__(self, database_class=None, **kwargs):
        # creating new struct
        if hasattr(self, "database_class") and kwargs != {}:
            values = ""
            final = []
            for k, v in kwargs.items():
                setattr(self, k, v)
            fields = Struct.getFields(self)
            keys = ", ".join(lst := list(fields))
            length = len(lst) - 1
            for i, value in enumerate(fields.values()):
                values += "?"
                values += ", " if i != length else ""
                boolean = isinstance(value, list) or isinstance(value, dict)
                final.append(value) if not boolean else final.append(jsonExtension.json.dumps(value))
            table_name = self.get_table_name()
            fields = Struct.uniqueField(self)
            expr = f"select * from {table_name} where "
            args = []
            expr, args = formAndExpr(expr, args, self, fields)
            selected = database_class.select_one_struct(expr, args, fromSerialized=self)
            if selected is None:
                database_class.execute(f"insert or ignore into {table_name} ({keys}) values ({values})", final)
            else:
                database_class.select_one_struct(expr, table_name, args, fromSerialized=self)
            self.database_class = database_class

    def __init_subclass__(cls):
        super().__init_subclass__()
        instance = cls()
        for x in Struct.must_implement:
            if not ListExtension(vars(instance)).includes(x):
                raise AttributeError(f"Class \"{instance}\" must implement property \"{x}\"")
        Struct.table_map[instance.get_table_name()] = cls
        Struct.class_poll.append(cls)

    def __setattr__(self, key: typing.Any, value: typing.Any):
        super().__setattr__(key, value)
        if hasattr(self, "database_class") and (
                db_class := attrgetter(getattr(self, "database_class"))) is not None and key != "database_class":
            db_class.write_struct(self, key, value)

    @staticmethod
    def toSqlite3Row(k, v):
        declaredValue = attrgetter(v)
        declaredType = Database.convert_type(declaredValue)
        row = f"{k} {declaredType} {adv_getter(v, 'type', '')} default \"{declaredValue}\""

        return row

    @staticmethod
    def toSqlite3Rows(cls):
        row = ""
        realDict = Struct.getFields(cls)
        dictKeys = list(realDict)
        for i, k in enumerate(dictKeys):
            v = cls.__dict__[k]
            row += Struct.toSqlite3Row(k, v)
            row += ", " if i != len(dictKeys) - 1 else ""
        return row

    @staticmethod
    def uniqueField(cls):
        if hasattr(cls, "save_by"): return attrgetter(cls.save_by)
        for k, v in Struct.getFields(cls).items():
            if isinstance(v, Sqlite3Property) and "unique" in v.type:
                return [k]

    def get_table_name(self):
        if hasattr(self, "table_name"):
            return attrgetter(getattr(self, "table_name"))
        else:
            return to_sneak_case(self.__class__.__name__)

    @staticmethod
    def getFields(cls):
        return {k: v for k, v in vars(cls).items() if not isinstance(v, ProtectedProperty) and k != "database_class"}

    def __del__(self):
        if hasattr(self, "database_class"):
            db_class = getattr(self, "database_class")
            table_name = self.get_table_name()
            fields = Struct.uniqueField(self)
            lst = []
            sql = f"delete from {table_name} where "
            sql, lst = formAndExpr(sql, lst, self, fields)
            db_class.execute(sql, lst)

    def __repr__(self):
        return f"{self.__class__.__name__}"


class Sqlite3Property(object):
    def __init__(self, x: typing.Any, y: typing.AnyStr):
        self.value = x
        self.type = y


class ProtectedProperty(object):
    def __init__(self, x: typing.Any):
        self.value = x


class Database(object):
    def __init__(self, file: typing.AnyStr, backup_folder: typing.AnyStr, bot_class, **kwargs):
        self.backup_folder = backup_folder
        self.file = file
        self.bot_class = bot_class
        self.db = sqlite3.connect(file, **kwargs)
        self.row_factory = sqlite3.Row
        self.db.row_factory = self.row_factory
        self.cursor = self.db.cursor()

        for struct in Struct.class_poll:
            struct = struct()
            tableName = struct.get_table_name()
            fields = Struct.getFields(struct)
            self.execute(f"create table if not exists {tableName} ({Struct.toSqlite3Rows(struct)})")
            tableFields = self.get_column_names(tableName)

            for field in fields:
                if field not in tableFields:
                    self.execute(
                        f"alter table {tableName} add column {Struct.toSqlite3Row(field, struct.__dict__[field])}")

        thread.every(self.bot_class.config["db_backup_interval"], name="Backup")(self.backup)

    def backup(self):
        if not self.bot_class.config["db_backups"]: return

        rawName = self.file.split("/")[-1]
        manager = thread.ThreadManager()
        manager.changeInterval("Backup", self.bot_class.config["db_backup_interval"])
        backup_table = sqlite3.connect(f"{self.backup_folder}backup_{timeExtension.now()}_{rawName}")
        self.db.backup(backup_table)

    def select(self, query: typing.AnyStr, args=[]):
        self.cursor.execute(query, args)
        return self.cursor.fetchall()

    def select_one(self, query: typing.AnyStr, *args):
        if isinstance(args, list):
            self.cursor.execute(query, list(map(str, args)))
        else:
            self.cursor.execute(query, *args)
        return self.cursor.fetchone()

    def write_struct(self, structToWrite: Struct, changedKey: typing.AnyStr, newValue: typing.Any):
        table = attrgetter(structToWrite.table_name)
        unique_fields = Struct.uniqueField(Struct.table_map[table]())
        sql = f"update or ignore {table} set {changedKey} = ? where "
        argsList = [newValue]
        sql, argsList = formAndExpr(sql, argsList, structToWrite, unique_fields)
        self.execute(sql, argsList)

    def select_one_struct(self, query: typing.AnyStr, *args, selectedStruct: Struct = None,
                          fromSerialized=None, table_name = None):
        table_name = self.parse_table_name(query, table_name)
        struct = self.select_one(query, *args) if selectedStruct is None else selectedStruct
        if not isinstance(table_name, str):
            raise Exception(
                f"Table name's type is not string (table_name was not provided correctly?)\n{query=}\n{args=}\n{table_name=}")
        myStruct = Struct.table_map[table_name]() if fromSerialized is None else fromSerialized
        unique_field = Struct.uniqueField(myStruct)
        if struct is None: return None
        for k in struct.keys():
            v = struct[k]
            attr = v
            data, value = jsonExtension.isDeserializable(v)
            if value:
                structByAction = jsonExtension.StructByAction(data)
                structByAction.action = partial(self.save_struct_by_action, table_name, k, structByAction, unique_field,
                                                myStruct)
                attr = structByAction
            setattr(myStruct, k, attr)
        myStruct.database_class = self
        return myStruct

    def select_all_structs(self, query: typing.AnyStr, table_name: typing.AnyStr, *args):
        structs = ListExtension.byList(self.select(query, *args))
        return list(map(lambda x: self.select_one_struct(query, table_name, *args, selectedStruct=x), structs))

    def save_struct_by_action(self, table_name: typing.AnyStr, key: typing.Any, value: typing.Any,
                              unique_field: typing.AnyStr, parent_struct: Struct, _):
        baseSql = f"update {table_name} set {key} = ? where "
        argsList = [jsonExtension.json.dumps(value.dictionary)]
        baseSql, argsList = formAndExpr(baseSql, argsList, parent_struct, unique_field)
        self.execute(baseSql, argsList)

    def execute(self, query: typing.AnyStr, args=[]):
        for i, k in enumerate(args):
            if type(k) is dict or type(k) is list:
                args[i] = jsonExtension.json.dumps(k)
            elif type(k) is jsonExtension.StructByAction:
                args[i] = jsonExtension.json.dumps(k.dictionary)
        self.cursor.execute(query, args)
        self.db.commit()
        return self.cursor

    def get_column_names(self, table: typing.AnyStr):
        return list(map(lambda x: x[0], self.cursor.execute(f"select * from {table}").description))

    def parse_table_name(self, query, fromCached = None):
        if fromCached is None:
            return list(tables_in_query(query))[0]
        return fromCached

    @staticmethod
    def convert_type(value):
        value_type = type(value)
        if value_type is str:
            return "text"
        elif value_type is float:
            return "real"
        elif value_type is None:
            return "null"
        elif value_type is int:
            return "int"
        elif value_type is dict:
            return "text"
        elif value_type is bool:
            return "bool"


db: Database = None

#https://grisha.org/blog/2016/11/14/table-names-from-sql/
def tables_in_query(sql_str):
    q = re.sub(r"/\*[^*]*\*+(?:[^*/][^*]*\*+)*/", "", sql_str)
    lines = [line for line in q.splitlines() if not re.match(r"^\s*(--|#)", line)]
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