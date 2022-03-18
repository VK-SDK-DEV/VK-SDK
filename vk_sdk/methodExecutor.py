from vk_api.exceptions import ApiError
from vk_api import VkApi


def empty(*args, **kwargs):
    """
    The empty function
    
    :param *args: Used to Pass a non-keyworded, variable-length argument list.
    :param **kwargs: Used to Pass a keyworded, variable-length argument list.
    :return: "none".
    """
    pass


class MethodExecutor(object):
    def __init__(self, vk, on_method_execute, on_error=None, method=None) -> None:
        self._method = method
        self.on_method_execute = on_method_execute or empty
        self.on_error = on_error or empty
        self._vk = vk

    def __getattr__(self, method):
        """
        The __getattr__ function is called when an attribute is not found in the usual places 
        (__dict__, class tree). It can bebe used to delegate the lookup to another object (usually either 
        the superclass or a mixin) and/or try some dynamic approach (e.g., see this recipe).
        
        :param self: Used to Access the class instance from within the method.
        :param method: Used to Determine which method is called.
        :return: A methodexecutor object.
        """
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])
        return MethodExecutor(
            self._vk,
            self.on_method_execute,
            self.on_error,
            (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        if self._method is not None:
            if self.on_method_execute is not None:
                shouldExecute = self.on_method_execute(self._method, kwargs)
                shouldExecute = shouldExecute or True
            if not shouldExecute:
                return
            self._vk._method = self._method
            try:
                tmpReturn = self._vk.__call__(**kwargs)
                return tmpReturn
            except Exception as e:
                self.on_error(e)
            finally:
                self._vk._method = None
                self._method = None


class AuthBasedMethodExecutor(MethodExecutor):
    def __init__(self, token, invalid_callback=None) -> None:
        """
        The __init__ function is called when a new instance of the class is created. 
        It initializes all of the variables in the class and can accept arguments that 
        are passed to it at creation time. In this case, we are creating an object that 
        contains a token and an invalid_callback function.
        
        :param self: Used to Reference the class instance itself.
        :param token: Used to Authenticate the user through VK.
        :param invalid_callback=None: Used to Specify a function to call when the token is invalid.
        :return: None.
        """
        self._valid = True
        self.invalid_callback = invalid_callback or empty
        vk = VkApi(token=token).get_api()
        super().__init__(vk, self.on_method_execute, self.on_error)

    def on_method_execute(self, *args, **kwargs):
        return self._valid

    def on_error(self, e):
        if isinstance(e, ApiError) and e.code == 5:
            self._valid = False
            self.invalid_callback()
