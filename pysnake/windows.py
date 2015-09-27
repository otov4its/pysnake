import curses

from . import settings


class WinWrapper(object):
    def __init__(self, win):
        self.win = win

    def __getattr__(self, item):
        return getattr(self.win, item)


class WinKeysWrapper(WinWrapper):
    def __init__(self, win, nodelay=True):
        super(WinKeysWrapper, self).__init__(win)
        self.keypad(1)
        self.nodelay(nodelay)
        self.key_code = None
        self.key_handlers = {}

    def getch(self, *args, **kwargs):
        self.key_code = self.win.getch(*args, **kwargs)
        return self.key_code

    def handle_key(self, key_code):
        if key_code in self.key_handlers:
            return self.key_handlers[key_code]() or True  # Retutn something if handler exists
        elif 'any' in self.key_handlers:
            return self.key_handlers['any']() or True  # Retutn something if handler exists
        else:
            curses.flushinp()  # Flush all input buffers to empty all unexpected input

    def getch_and_handle(self):
        self.key_code = self.getch()
        result = self.handle_key(self.key_code)
        return self.key_code, result

    def bind(self, key_codes, callback):
        if key_codes == 'any':
            self.key_handlers['any'] = callback
        elif isinstance(key_codes, int):
            self.bind_key(key_codes, callback)
        else:
            for key_code in key_codes:
                self.bind_key(key_code, callback)

    def bind_key(self, key_code, callback):
        if not isinstance(key_code, int):
            key_code = ord(key_code)
        self.key_handlers[key_code] = callback

    def unbind(self, key_code):
        del self.key_handlers[key_code]

    def get_keys(self):
        return self.key_handlers.keys()


class PopupWindow(object):
    def __init__(self, parent, message, modal=True):
        self.parent = parent

        self.message = message
        self.message_info = self.__process_message()

        self.modal = modal

        self.popup_win = WinKeysWrapper(curses.newwin(*self.__compute_sizes()), nodelay=False)
        self.popup_win.border()

    def __getattr__(self, item):
        return getattr(self.popup_win, item)

    def __process_message(self):
        message_info = dict()
        message_info['lines'] = self.message.splitlines()
        message_info['lines_count'] = len(message_info['lines'])
        message_info['max_row_length'] = max(map(len, message_info["lines"]))
        return message_info

    def __compute_sizes(self):
        parent_y, parent_x = self.parent.getmaxyx()

        center_y = int(round((parent_y - self.message_info['lines_count']) / 2)) - 1
        center_x = int(round((parent_x - self.message_info['max_row_length']) / 2)) - 1
        if center_y < 0:
            center_y = 0
        if center_x < 0:
            center_x = 0

        height = self.message_info['lines_count'] + 2
        width = self.message_info['max_row_length'] + 4
        if height > parent_y:
            height = parent_y
        if width > parent_x:
            width = parent_x

        self.height = height
        self.width = width

        return height, width, center_y, center_x

    def show(self):
        width = self.width - 4
        height = self.height - 2
        for row in range(height):
            self.addnstr(1 + row, 2, self.message_info['lines'][row].center(width), width, curses.A_REVERSE)
        self.refresh()
        if self.modal:
            self.wait_key()

    def propagate_key(self):
        self.parent.handle_key(self.key_code)

    def wait_key(self):
        while True:
            if self.getch_and_handle()[1]:
                break


class GameQuitPopup(PopupWindow):
    def __init__(self, parent, message='Bye!', modal=False):
        super(GameQuitPopup, self).__init__(parent, message, modal)


class GameOverPopup(PopupWindow):
    def __init__(self, parent, message='Game Over', modal=True):
        super(GameOverPopup, self).__init__(parent, message, modal)
        parent_keys = set(parent.get_keys())
        move_keys = {settings.MOVE_DOWN, settings.MOVE_RIGHT, settings.MOVE_UP, settings.MOVE_LEFT}
        pause_keys = set(map(ord, settings.KEYS_PAUSE))
        self.bind(parent_keys - move_keys - pause_keys, self.propagate_key)


class GameWinPopup(GameOverPopup):
    def __init__(self, parent, message='Win!', modal=True):
        super(GameWinPopup, self).__init__(parent, message, modal)


class GamePausePopup(PopupWindow):
    def __init__(self, parent, message='Pause\npress any key', modal=True):
        super(GamePausePopup, self).__init__(parent, message, modal)
        self.bind('any', lambda: 0)
        self.bind(curses.KEY_RESIZE, self.propagate_key)


class GameRewindPopup(GamePausePopup):
    def __init__(self, parent, message='Rewind mode\npress "r"', modal=True):
        super(GameRewindPopup, self).__init__(parent, message, modal)
        self.bind(settings.KEYS_REWIND, self.propagate_key)
