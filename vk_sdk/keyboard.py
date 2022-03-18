from .listExtension import ListExtension
import random

from vk_api import keyboard

from .jsonExtension import StructByAction


class Keyboard(keyboard.VkKeyboard):
    colors = {"blue": "primary", "white": "default",
              "red": "negative", "green": "positive"}

    def __init__(self, buttons=None, strategy="default", one_time=False, inline=False):
        """
        The __init__ function is called when a new object is created from the class.
        The __init__ function can take arguments, but self is always the first one.
        Self is just a reference to the instance of the class. It's automatically 
        passed in when you instantiate an instance of the class.
        
        :param self: Used to Refer to the object itself.
        :param buttons=None: Dict/List/str describing buttons.
            could be Dict:
                        name       color
                :code:`{"button1": "red"}`
            could be List:
                         name
                :code:`["button1", "button2"]`
            could be str:
                         name
                :code:`"button_name"`
            for list and str we use random colors
        :param strategy="default": Used to Set the default strategy for handling append on the buttons.
        :param one_time=False: Used to Specify if the keyboard should be removed after one response.
        :param inline=False: Used to Specify whether the buttons should be bounded to a message.
        :return: The object of the class.
        """
        if buttons is None:
            buttons = []
        self.strategy = strategy
        super().__init__(one_time=one_time, inline=inline)
        self.button_index = 0
        if isinstance(buttons, list) or isinstance(buttons, ListExtension):
            self.add_from_list(buttons)
        elif type(buttons) is dict:
            self.add_from_dict(buttons)
        elif type(buttons) is str:
            self.add_button(buttons, color="green")
        elif isinstance(buttons, StructByAction):
            self.add_from_list(buttons.dictionary)

    @classmethod
    def byKeyboard(cls, newKb):
        """
        The byKeyboard function is a class method that returns an instance of the Keyboard class. 
        It takes one argument, newKb, which is either another Keyboard object. If newKb is not already a Keyboard object it will be passed to the constructor.
        
        :param cls: Used to Pass the class of the object that is being created.
        :param newKb: Used to Pass in a new keyboard object.
        :return: A new instance of the keyboard class.
        """
        if isinstance(newKb, cls):
            return newKb
        else:
            return cls(newKb)

    def get_keyboard(self):
        """Cleanups empty lines and returns keyboard as json"""
        self.cleanup_empty()
        return super().get_keyboard()

    @classmethod
    def get_empty_keyboard(cls):
        return cls()

    def add_button(self, *args, **kwargs):
        if getattr(Strategies, self.strategy)(self):
            self.add_line()
        args = list(args)
        if len(args) >= 2:
            color = args[1]
            del args[1]
        else:
            color = kwargs.get("color")
        if color is not None:
            if color in self.colors:
                color = self.colors[color]
        else:
            color = self.colors["white"]
        kwargs["color"] = color
        super().add_button(*args, **kwargs)
        self.button_index += 1
        return self

    def cleanup_empty(self):
        for i, line in enumerate(self.lines):
            if not line:
                del self.lines[i]

    def add_line(self):
        """
        The add_line function adds a line to the Keyboard.
        It also removes any empty lines from the Keyboard.
        
        :param self: Used to Refer to the object itself.
        :return: None.
        """
        self.cleanup_empty()
        self.button_index = 0
        super().add_line()
        return self

    def add_from_list(self, arr):
        for j in arr:
            if j != "locationButton":
                self.add_button(j, color=self.get_random_color())
            else:
                self.add_location_button()
                self.add_line()

    def add_from_dict(self, d):
        if (strategy := d.get('strategy')) is not None:
            self.strategy = strategy
            del d['strategy']
        for k, v in d.items():
            if v == "line":
                self.add_line()
            else:
                self.add_button(k, v)

    def get_random_color(self):
        """
        The get_random_color function returns a random color.
        
        :returns: A random color from `Keyboard.colors`:
        
        :param self: Used to Access variables that belongs to the class.
        """
        return random.choice(list(self.colors))

    def __repr__(self):
        return self.get_keyboard()

    # += operator
    def __iadd__(self, other):
        return self.__add__(other)

    def __add__(self, other):
        if isinstance(other, dict):
            self.add_from_dict(other)
        elif isinstance(other, list):
            self.add_from_list(other)
        else:
            self.add_button(other, color=self.get_random_color())
        return self


class Strategies(object):
    @staticmethod
    def default(keyboard: Keyboard):
        return keyboard.button_index % 4 == 0

    @staticmethod
    def insert_lines(_):
        return True

    @staticmethod
    def max_two_buttons(keyboard: Keyboard):
        return keyboard.button_index % 2 == 0
