import json
from .jsonExtension import ExtensionBase

class ListExtension(ExtensionBase, list):
    def __new__(cls, other=None, saver=None):
        if isinstance(other, cls):
            return other
        return super().__new__(cls)

    def find(self, lmbd, *args, **kwargs):
        for item in self:
            if lmbd(item, *args, **kwargs):
                return item

    def join(self, separator: str, prefix="", postfix=""):
        string = ""
        for iterable, item in enumerate(self):
            string = f"{string}{prefix}{item}{postfix}"
            if iterable + 1 != len(self):
                string += separator
        return string

    def __call__(self):
        return ListExtension()

    def findall(self, lmbd, *args, **kwargs):
        lst = self()
        for item in self:
            if lmbd(item, *args, **kwargs):
                lst.append(item)
        return lst

    @classmethod
    def indexList(cls, list=None):
        iterate = list or cls
        l = cls()
        for index in range(len(iterate)):
            l.append(index)
        return l

    def all(self, function, *args, **kwargs):
        """
        The all function takes a function and it's additional argumes. 
        It returns True if the function(element, *args, **kwargs) evaluates to True for every element of the iterable, False otherwise.
        
        :param self: Used to Call the function on each element in the list.
        :param function: Used to Specify the function that is to be called on each element of the iterable.
        :param *args: Used to Pass a non-keyworded, variable-length argument list.
        :param **kwargs: Used to Pass keyworded, variable-length argument lists to the function.
        """
        for i in self:
            if not function(i, *args, **kwargs):
                return False
        return True

    def has(self, item, returnIndex=False):
        for i, iterator in enumerate(self):
            if hasattr(iterator, "has") and callable(iterator.has):
                if iterator.has(item):
                    return True if not returnIndex else i
            if iterator == item:
                return True if not returnIndex else i
        return False if not returnIndex else -1

    def indexOf(self, item):
        return self.has(item, True)

    def first(self):
        return self.get(0)

    def __getitem__(self, key):
        if isinstance(key, slice) or key < len(self):
            return list.__getitem__(self, key)
        return None

    get = __getitem__

    def filter(self, lmbd):
        instance = ListExtension()
        for i in self:
            if lmbd(i):
                instance.append(i)
        return instance

    @staticmethod
    def accept(data):
        return json.loads(data)

    def forEach(self, lmbd):
        for item in self:
            lmbd(item)

    def includes(self, value):
        return value in self

    @classmethod
    def byList(cls, lst):
        return cls(lst)

    def append(self, value):
        super().append(value)
        self.save()
        return self

    def copy(self):
        return ListExtension(self)

    def map(self, lmbd, *args):
        save = self()
        for element in self:
            save.append(lmbd(element, *args))
        return save

    def __add__(self, other):
        if type(other) is list:
            self += other
            self.save()
        else:
            self.append(other)
        return self
