from vk_api.exceptions import ApiError

from .methodExecutor import MethodExecutor
from .keyboard import Keyboard
import vk_api
from vk_api import VkUpload
from . import thread
from .cmd import set_after

class User(MethodExecutor):
    # method to insert keyword map
    user_id_methods = {
        "messages.getHistory": "user_id", "users.get": "user_ids"}

    def __new__(cls, user_id, fields = None, **kwargs):
        """
        The __new__ function is the method called before __init__, it's used to create an instance of a class.
        It takes in cls (the class) as the first argument and returns an instance of that class.
        The __new__ function is also allowed to modify attributes on cls before returning the new object.
        
        :param cls: Used to Refer to the class, not the instance.
        :param user_id: Used to Specify the user whose data we want to get.
        :param fields=None: Used to Get the fields from the vk api.
        :param **kwargs: Used to Pass parameters to the __init__ function.
        :return: A user instance if user_id was a valid user id, otherwise None.
        """
        try:
            if fields is None:
                fields = "photo_id,photo_50"
            vk = kwargs.get("vk")
            instance = super(User, cls).__new__(cls)
            if vk is None:
                vk = thread.main_thread.vk
                kwargs["vk"] = vk
            instance.vk = vk
            get = vk.users.get(user_ids=user_id, fields=fields)[0]
            instance.request = get
            return instance
        except:
            return None

    def __init__(self, user_id=None, fields = None, vk=None):
        """
        The __init__ function is called when an instance of the class is created. 
        It initializes all of the variables that are defined in the __init__ function, 
        and it sets them to their passed-in values. In this case, we're setting self.avatar = avatar and self.user_name = user_name.
        
        :param self: Used to Refer to the object itself.
        :param user_id=None: Used to Specify the user id.
        :param fields=None: Used to Specify the fields that will be returned by the api.
        :param vk=None: Used to Pass the vk object to the class.
        """
        self.avatar = f"photo{self.request['photo_id']}" if self.request.get(
            'photo_id') is not None else ""
        self.user_name = f"{self.request['first_name']} {self.request['last_name']}"
        self.id = str(self.request["id"])

        super().__init__(self.vk, self.on_method_execute)

    def write(self, message, keyboard=None, after=None, after_args=None, **kwargs):
        """Method to write a user

        Args:
            message (str): message content
            keyboard (:class:`Keyboard`, optional): Keyboard to send.
            after (str, optional): After function to ser.
            after_args (str, optional): Arguments for after function.
        """     
        if keyboard is not None:
            kwargs["keyboard"] = Keyboard.byKeyboard(keyboard)
        try:
            self._vk.messages.send(user_id=self.id, message=message, random_id=vk_api.utils.get_random_id(),
                                   **kwargs)
        except ApiError:
            pass
        finally:
            if after is not None:
                set_after(after, self.id, after_args)

    def on_method_execute(self, method, kwargs):
        if method in User.user_id_methods:
            kwargs[User.user_id_methods[method]] = self.id

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, type(self)):
            raise NotImplementedError
        return self.id == o.id

    def __hash__(self) -> int:
        return int(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

    @property
    def mention(self):
        return f"@id{self.id}({self.user_name})"
