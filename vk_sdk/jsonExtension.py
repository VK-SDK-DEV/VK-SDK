import json
import os


class ExtensionBase(object):

    classes = {}

    def __init_subclass__(cls) -> None:

        for cl in cls.mro():
            if cl not in (cls, ExtensionBase):
                cls.classes[cls] = cl
                cls._subclassing = cl
                break

    def __init__(self, iterable=None, saver=None):
        super().__init__(iterable) if iterable is not None else super().__init__()
        self.saver = saver

    def __getitem__(self, item):
        result = self.get(item)
        klass = StructByAction.get_class(result, init=False, saver=self.saver)
        if not isinstance(result, tuple(ExtensionBase.classes)):
            klass = StructByAction.get_class(result, saver=self.saver)
            self.setitem(item, klass, False)
            return klass
        return result

    @classmethod
    def accept(cls, data, **init_kwargs):
        for cls in cls.classes:
            if isinstance(data, cls):
                return data
            elif (clsm := getattr(cls, "accept", None)) is not None:
                try:
                    return StructByAction(clsm(data), **init_kwargs)
                except Exception:
                    continue
        return data

    def __setitem__(self, item, value, save=True):
        super().__setitem__(item, value)
        if save:
            self.save()

    def __delitem__(self, item):
        super().__delitem__(item)
        self.save()

    setitem = __setitem__

    def save(self):
        if self.saver is not None:
            self.saver.save()


class DictExtension(ExtensionBase, dict):
    @staticmethod
    def accept(data):
        return json.loads(data)


class StructByAction(object):

    __slots__ = "saver", "use_class"

    def __new__(cls, initData, saver=None):
        if type(initData) == type(cls.get_class(initData, init=False)):
            raise ValueError
        self_ins = super().__new__(cls)
        self_ins.saver = saver
        self_ins.use_class = cls.get_class(initData, saver=self_ins)
        return self_ins.use_class

    @staticmethod
    def get_class(data, *args, init=True, **kwargs):
        for klass in ExtensionBase.classes:
            if isinstance(data, klass._subclassing):
                return klass(data, *args, **kwargs) if init else klass
        return data

    def save(self):
        if self.saver is not None:
            self.saver(self.use_class)


def save(file, obj, indent=None):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent)


def load(file, indent=None):
    with open(file, encoding="utf-8") as f:
        return StructByAction(json.load(f), saver=lambda d: save(file, d, indent))


def loadAdvanced(file, ident=None, content=None):
    if content is not None and not os.path.exists(file):
        _dir = os.path.dirname(file)
        _dir and os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            content = json.dumps(content) if isinstance(
                content, dict) else content
            f.write(content)
    return load(file, ident)
