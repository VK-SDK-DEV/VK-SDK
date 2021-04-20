class ListExtension(list):

    def __init__(self, other=None):
        if other is None:
            other = []
        super().__init__(other)

    def find(self, lmbd, *args, **kwargs):
        for item in self:
            if lmbd(item, *args, **kwargs):
                return item

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
    
    def map(self, lmbd, *args, **kwargs):
        
        for i, _ in enumerate(self):
            self[i] = lmbd(*args, **kwargs)

    def __add__(self, other):
        if type(other) is list:
            self += other
        else:
            self.append(other)
        return self