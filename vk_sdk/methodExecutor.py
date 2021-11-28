class MethodExecutor(object):
    def __init__(self, vk, on_method_execute, method=None) -> None:
        self._method = method
        self.on_method_execute = on_method_execute
        self._vk = vk
        #super().__init__()

    def __getattr__(self, method):  # str8 up
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])
        return MethodExecutor(
            self._vk,
            self.on_method_execute,
            (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        if self._method is not None:
            if self.on_method_execute is not None:
                self.on_method_execute(self._method, kwargs)
            self._vk._method = self._method
            tmpReturn = self._vk.__call__(**kwargs)
            # set to null
            self._vk._method = None
            self._method = None
            return tmpReturn
