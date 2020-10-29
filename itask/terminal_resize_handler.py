import signal


class TerminalResizeListener:

    _instance = None

    def __new__(cls):
        if TerminalResizeListener._instance is None:
            TerminalResizeListener._instance = object.__new__(cls)

        return TerminalResizeListener._instance

    def __init__(self):
        self._listeners = list()

        signal.signal(signal.SIGWINCH, self._handler)

    def _handler(self, signum, stack):
        for listener in self._listeners:
            listener()

    def register_listener(self, handler):
        self._listeners.append(handler)

    def unregister_listener(self, handler):
        self._listeners.remove(handler)
