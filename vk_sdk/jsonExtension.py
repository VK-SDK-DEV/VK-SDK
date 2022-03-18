import json
import os
from typing import Callable


class StructByAction(object):
    def __init__(self, initDict, parent=None, parent_key=None, action: Callable = lambda _: _):
        """
        The __init__ function is called when a new instance of the class is created. 
        It initializes the attributes of the class, and sets up any parameters that are needed to create an instance of this object. 
        The __init__ function can take arguments (self, other_arguments), but self is always required as it refers to itself - in this case, 
        it refers to an instance of a particular object.
        
        :param self: Used to Refer to the instance of the class.
        :param initDict: Used to Initialize the dictionary of the node.
        :param parent=None: Used to Set the parent of the node.
        :param parent_key=None: Used to Store the key of the parent node in a recursive call.
        :param action:Callable=lambda_:_: Used to Define the action that will be taken when a node is updated.
        :return: The object itself.
        """
        self.parent = parent
        self.dictionary = initDict
        self.parent_key = parent_key
        self.action = action

    def __setitem__(self, key, value):
        """
        The __setitem__ function is a special method that allows us to use the square bracket notation on our class. 
        The __setitem__ function is called when we use the square bracket notation on an object, and it takes two arguments: self and key. 
        The self argument represents the instance of the object itself, which in this case will be a DictionaryHandler instance. The key argument will be whatever is inside of our brackets after we call __setitem__.
        
        :param self: Used to Refer to the object instance.
        :param key: Used to Specify the key of the element in the dictionary that is to be changed.
        :param value: Used to Set the value of a key in the dictionary.
        :return: None.
        """
        if self.parent is None:
            self.dictionary.__setitem__(key, value)
            self.action(self.dictionary)
        else:
            self.dictionary[key] = value
            self.parent.__setitem__(self.parent_key, self.dictionary)

    def __getitem__(self, key):
        tmp_return = self.dictionary[key]
        if isinstance(tmp_return, dict) or isinstance(tmp_return, list):
            return StructByAction(tmp_return, parent=self, parent_key=key, action=self.action)
        else:
            return tmp_return

    def __iter__(self):
        return self.dictionary.__iter__()

    def get(self, key):
        return self.dictionary[key]

    def __str__(self):
        return self.dictionary.__str__()

    def __repr__(self):
        return f"StructByAction({self.dictionary})"

    def __delitem__(self, item):
        del self.dictionary[item]
        self.action(self.dictionary)

    def __contains__(self, item):
        return self.dictionary.__contains__(item)

    # list methods
    def __len__(self):
        return len(self.dictionary)

    def append(self, value):
        self.dictionary.append(value)
        self.action(self.dictionary)

    def __iadd__(self, keys):
        self.dictionary += keys
        self.action(self.dictionary)
        return self

    def insert(self, index, value):
        self.dictionary.insert(index, value)
        self.action(self.dictionary)
        return self

    def __bool__(self):
        return len(self.dictionary) > 0 if isinstance(self.dictionary, list) else len(self.dictionary.keys()) > 0


def save(file, obj, indent=None):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent)


def load(file, indent=None):
    with open(file, encoding="utf-8") as f:
        return StructByAction(json.load(f), action=lambda d: save(file, d, indent))


def loadAdvanced(file, ident=None, content=None):
    if content is not None and not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            content = json.dumps(content) if isinstance(content, dict) else content
            f.write(content)
    return load(file, ident)


def isCastToFloatAvailable(data):
    try:
        float(data)
        return True
    except ValueError:
        return False


def isDeserializable(data):
    try:
        if isCastToFloatAvailable(data) or not (data.startswith("{") or data.startswith("[")):
            return {}, False
        return json.loads(data), True
    except (ValueError, TypeError):
        return {}, False
