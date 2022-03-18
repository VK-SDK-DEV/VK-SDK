class ListExtension(list):
    def __new__(cls, other=None):
        if isinstance(other, cls):
            return other
        return super().__new__(cls)

    def __init__(self, other=None):
        if other is None:
            other = []
        super().__init__(other)

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
        iterate = getattr(list, "dictionary", list) or cls
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
        return self[0]

    def __getitem__(self, key):
        if isinstance(key, slice):
            return super().__getitem__(key)
        if key < len(self):
            return super().__getitem__(key)
        return None

    def filter(self, lmbd):
        instance = ListExtension()
        for i in self:
            if lmbd(i):
                instance.append(i)
        return instance

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
        return self

    def copy(self):
        return ListExtension(self)

    def map(self, lmbd, copy=False, *args, **kwargs):
        save = self if not copy else self()
        for i, _ in enumerate(self):
            if copy:
                save.append(lmbd(_, *args, **kwargs))
            else:
                save[i] = lmbd(_, *args, **kwargs)
        return save

    def __add__(self, other):
        if type(other) is list:
            self += other
        else:
            self.append(other)
        return self
