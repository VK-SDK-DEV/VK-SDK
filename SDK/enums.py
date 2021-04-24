import inspect
from SDK.dataClass import DataClass


# kotlin-like enums
class Enum(object):
    def __init_subclass__(cls):
        super().__init_subclass__()
        inspectedArgs = inspect.getfullargspec(cls.__init__)
        cls.EnumValue = DataClass(*inspectedArgs.args[1:])
