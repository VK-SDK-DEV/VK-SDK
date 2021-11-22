from vk_api.exceptions import ApiError

from SDK.methodExecutor import MethodExecutor
from .keyboard import Keyboard
import vk_api
from . import thread
from .cmd import set_after

class User(MethodExecutor):
    # method to insert keyword map
    user_id_methods = {
        "messages.getHistory": "user_id", "users.get": "user_ids"}

    def __new__(cls, user_id, fields = None, **kwargs):
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
        self.avatar = f"photo{self.request['photo_id']}" if self.request.get(
            'photo_id') is not None else ""
        self.user_name = f"{self.request['first_name']} {self.request['last_name']}"
        self.id = str(self.request["id"])

        super().__init__(self.vk, self.on_method_execute)

    def write(self, message, keyboard=None, after=None, after_args=None, **kwargs):
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

    @property
    def mention(self):
        return f"@id{self.id}({self.user_name})"
