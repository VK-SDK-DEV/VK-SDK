import vk_api

class User(object):
    user_id_methods = ["messages.getHistory"]

    def __init__(self, vk, user_id, method=None):
        self._vk = vk
        self._method = method
        self.id = user_id

    def write(self, message, **kwargs):
        return self._vk.messages.send(user_id=self.id, message=message, random_id=vk_api.utils.get_random_id(),
                                      **kwargs)

    def __getattr__(self, method):  # str8 up
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])
        return User(
            self._vk,
            self.id,
            (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        if self._method in User.user_id_methods:
            kwargs["user_id"] = self.id
        self._vk._method = self._method
        return self._vk.__call__(**kwargs)
