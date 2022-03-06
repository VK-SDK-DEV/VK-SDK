import os

from importlib import util
import importlib


class ImportTools(object):
    ignore = ["__pycache__"]
    imported = []
    modules = {}

    def __init__(self, paths=None):
        if paths is None:
            paths = ["packages"]
        for path in paths:
            if path in self.imported:
                continue
            if not os.path.exists(path):
                os.makedirs(path)
            for file in os.listdir(path):
                if path in self.ignore:
                    continue
                thisPath = os.path.join(path, file)
                if os.path.isdir(thisPath):
                    continue
                self.imp_by_path(thisPath)
                self.imported.append(path)

    def reload(self, module):
        for k, v in self.modules.items():
            if k == module:
                self.modules[k] = importlib.reload(v)

    def reload_all(self):
        for k, v in self.modules.items():
            self.modules[k] = importlib.reload(v)

    @classmethod
    def imp_by_path(cls, path):
        if not path.endswith(".py"):
            path += ".py"
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = util.spec_from_file_location(module_name, path)
        foo = util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        cls.modules[path.replace(os.path.sep, "/")] = foo
        return foo


require = ImportTools.imp_by_path