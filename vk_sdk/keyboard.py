import random

from vk_api import keyboard


class Keyboard(keyboard.VkKeyboard):
    colors = {"blue": "primary", "white": "secondary",
              "red": "negative", "green": "positive"}

    def __new__(cls, buttons=None, **kwargs):
        if isinstance(buttons, cls):
            return cls
        return super().__new__(cls)

    def __init__(self, buttons=None, strategy="default", **kwargs):
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
        super().__init__(**kwargs)
        self.button_index = 0
        self.__add__(buttons)

    def get_keyboard(self):
        """Cleanups empty lines and returns keyboard as json"""
        self.cleanup()
        return super().get_keyboard()

    __repr__ = get_keyboard

    @classmethod
    def empty(cls):
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

    def cleanup(self):
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
        self.cleanup()
        self.button_index = 0
        super().add_line()
        return self

    def add_from_list(self, arr):
        for j in arr:
            if j != "locationButton":
                self.add_button(j, color=self.random_color())
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

    def random_color(self):
        """
        The get_random_color function returns a random color.

        :returns: A random color from `Keyboard.colors`:

        :param self: Used to Access variables that belongs to the class.
        """
        return random.choice(list(self.colors))

    def __add__(self, other):
        if isinstance(other, dict):
            self.add_from_dict(other)
        elif isinstance(other, list):
            self.add_from_list(other)
        elif isinstance(other, str):
            self.add_button(other, color=self.random_color())
        return self

    __iadd__ = __add__


class Strategies:
    @staticmethod
    def default(keyboard: Keyboard):
        return keyboard.button_index % 4 == 0

    @staticmethod
    def insert_lines(_):
        return True

    @staticmethod
    def max_two(keyboard: Keyboard):
        return keyboard.button_index % 2 == 0

    max_two_buttons = max_two

    @staticmethod
    def max_five(keyboard: Keyboard):
        return keyboard.button_index % 5 == 0
