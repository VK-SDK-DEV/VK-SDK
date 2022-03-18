import os
from importlib import util
import importlib
import pathlib
from types import ModuleType
import inspect


class ImportOrder(object):
    orders = {}
    file_name = "__import_order__.py"

    def __init__(self, *names, sort_files=False, file = None) -> None:
        file = file or inspect.stack()[1].filename
        self.order = []
        names = [
            name + ".py" if not name.endswith(".py") else name for name in names]
        self.order += names
        names = set(names)
        parent = pathlib.Path(file).parent.resolve()
        root = pathlib.Path(os.path.abspath(os.curdir))
        rel_path = str(parent.relative_to(root))
        files = os.listdir(parent)
        if sort_files:
            files.sort()
        for file in files:
            if file not in names:
                self.order.append(file)
        self.orders[rel_path] = self

    @classmethod
    def resolve(cls, path):
        lsdir = os.listdir(path)
        if cls.file_name in lsdir:
            require(f"{path}/{cls.file_name}")
            return cls.orders[path].order
        else:
            return lsdir


class ImportTools(object):
    ignore = ["__pycache__"]
    imported = set()
    import_queue = set()
    modules = {}

    def __init__(self, paths=None):
        if paths is None:
            paths = ["packages"]
        for path in paths:
            if path in self.imported or path in self.import_queue:
                continue
            self.import_queue.add(path)
            if not os.path.exists(path):
                os.makedirs(path)
            for file in ImportOrder.resolve(path):
                if path in self.ignore:
                    continue
                thisPath = os.path.join(path, file)
                if os.path.isdir(thisPath):
                    continue
                self.imp_by_path(thisPath)
            self.import_queue.remove(path)
            self.imported.add(path)

    def reload(self, module):
        """
        The reload function reloads a module. It takes in the name of the module as an argument and reloads it.
        
        :param self: Used to Reference the class object.
        :param module: Used to Specify the module that is to be reloaded.
        :return: The module that was reloaded.
        """
        for k, v in self.modules.items():
            if k == module:
                self.modules[k] = importlib.reload(v)

    def reload_all(self):
        """
        The reload_all function reloads all of the modules.
        
        :param self: Used to Access the attributes and methods of the class in which it is used.
        """
        for k, v in self.modules.items():
            self.modules[k] = importlib.reload(v)

    @classmethod
    def imp_by_path(cls, path) -> ModuleType:
        """
        The imp_by_path function imports a Python module from a path. Like a node.js' require 
        
        :param cls: Used to Access the class attributes.
        :param path: Used to Specify the path of the module.
        :return: The module that was loaded from the path.
        """
        if not path.endswith(".py"):
            path += ".py"
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = util.spec_from_file_location(module_name, path)
        foo = util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        cls.modules[path.replace(os.path.sep, "/")] = foo
        return foo


require = ImportTools.imp_by_path
