"""A tiny stand-in for Streamlit, used only by the tests.

It lets the tests run app.py from top to bottom without a browser and without
Streamlit installed. Every call such as st.markdown("...") is simply recorded
so a test can check what the app tried to show.

This is NOT a replacement for running the real app: it cannot detect layout
problems. Always also run `streamlit run app.py` and click through the tabs.
"""

import sys
import types


class _Block:
    """Something usable in a `with` statement (tab, column, expander, form...)."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = {}
        self.calls = []          # (function name, first argument) for every call
        self.inputs = {}         # label -> value returned by an input widget
        self.clicked = set()     # labels of buttons that should report "clicked"

    # --- helpers used by the tests -------------------------------------
    def shown(self, name=None):
        """All text shown so far, optionally only from one function."""
        return "\n".join(str(text) for call, text in self.calls if name in (None, call))

    def reset_output(self):
        self.calls = []

    def _record(self, name, args):
        self.calls.append((name, args[0] if args else ""))

    # --- caching decorators: just call the function ---------------------
    def cache_data(self, func=None, **kwargs):
        return func if func else (lambda inner: inner)

    cache_resource = cache_data

    # --- layout ----------------------------------------------------------
    def tabs(self, names):
        self._record("tabs", [", ".join(names)])
        return [_Block() for _ in names]

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_Block() for _ in range(count)]

    def container(self, *args, **kwargs):
        return _Block()

    def expander(self, *args, **kwargs):
        self._record("expander", args)
        return _Block()

    def form(self, *args, **kwargs):
        return _Block()

    def chat_message(self, *args, **kwargs):
        self._record("chat_message", args)
        return _Block()

    @property
    def sidebar(self):
        return _Block()

    # --- input widgets ---------------------------------------------------
    def text_area(self, label, *args, **kwargs):
        return self.inputs.get(label, "")

    def selectbox(self, label, options, *args, **kwargs):
        return self.inputs.get(label, options[0])

    def radio(self, label, options, *args, **kwargs):
        return self.inputs.get(label, options[0])

    def multiselect(self, label, options, default=None, **kwargs):
        return self.inputs.get(label, default or [])

    def slider(self, label, min_value=None, max_value=None, value=None, **kwargs):
        return self.inputs.get(label, value)

    def button(self, label, *args, on_click=None, args_=None, **kwargs):
        clicked = label in self.clicked
        if clicked and on_click:
            on_click(*kwargs.get("args", ()))
        return clicked

    def form_submit_button(self, label, *args, **kwargs):
        return label in self.clicked

    def download_button(self, label, data=None, **kwargs):
        self._record("download_button", [data])
        return False

    # --- anything else (title, markdown, info, warning, ...) is recorded --
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)

        def record(*args, **kwargs):
            self._record(name, args)

        return record


def install():
    """Put the fake module in place of `streamlit` and return it."""
    fake = FakeStreamlit()
    sys.modules["streamlit"] = fake
    return fake
