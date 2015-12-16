# -*- coding: utf-8 -*-"""

def get_clipboard(request, key=None):
    clipboard = request.session.get("clipboard", None)
    if not clipboard:
        clipboard = {}
    if key:
        return clipboard.get(key, None)
    else:
        return clipboard

def set_clipboard(request, key=None, value=None):
    clipboard = get_clipboard(request)
    if key:
        if value:
            clipboard[key] = value
        elif clipboard.get(key, None):
            del clipboard[key]
    request.session["clipboard"] = clipboard

