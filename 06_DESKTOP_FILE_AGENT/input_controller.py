from errors import E


class CancellationToken:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class InputController:
    """Wraps adapter.click/type with the 6.17 guard: never send input
    without first validating the expected active window/application."""

    def __init__(self, adapter, desktop, sid, expected_app):
        self.adapter = adapter
        self.desktop = desktop
        self.sid = sid
        self.expected_app = expected_app

    def _guard(self, token=None):
        if token is not None and token.cancelled:
            raise RuntimeError(E.ACTION_TIMEOUT)
        # Raises WINDOW_NOT_FOUND if some other application is foreground,
        # preventing input meant for `expected_app` reaching the wrong one.
        self.desktop.verify_foreground(self.sid, self.expected_app)

    def click(self, target, token=None):
        if target is None:
            raise RuntimeError(E.INPUT_TARGET_UNCERTAIN)
        self._guard(token)
        return self.adapter.click(target)

    def type(self, text, token=None):
        self._guard(token)
        return self.adapter.type(text)
