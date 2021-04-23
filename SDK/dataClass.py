class DataClass(object):
    def __init__(self, *args):
        self.args = args
        for i in args:
            self.__setattr__(i, None)

    def __call__(self, *args):
        newInstance = DataClass(*self.args)
        for j, i in enumerate(self.args):
            newInstance.__setattr__(i, args[j])
        return newInstance
