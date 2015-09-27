import sys
import time
import curses
import pickle
from collections import deque
import copy

from .arena import Arena, BlockEfir, BlockSnake, BlockFood, BlockBorder
from . import settings, windows
from .exeptions import *


class Zoom(object):
    def __init__(self, factor=settings.ZOOM_FACTOR):
        self.factor = factor
        self.x = 1  # Zoom factor for x absciss
        self.y = 1  # Zoom factor for y ordinate

    def in_(self, n=1):
        """Zoom in"""
        self.y += n
        self.__calc_x()
        return self

    def out(self, n=1):
        """Zoom out"""
        self.y -= n
        if self.y < 1:
            self.y = 1
        self.__calc_x()
        return self

    def auto(self, width, height, base=75.0):
        """Auto zoom"""
        value = min(width, height * self.factor)
        zoom_in = int(round(value / base))
        self.in_(zoom_in)
        return self

    def __calc_x(self):
        """Calculate x accordingly for y and zoom factor"""
        if self.y == 1:  # Base mode without zooming
            self.x = 1
        else:
            self.x = int(round(self.y * self.factor))


class Game(object):
    def __init__(self, stdscr, zoom=None):
        # Rewind feature data structure
        global snapshots
        snapshots = deque(maxlen=11)

        # Curses settings
        self.adjust_curses()

        # Curses stdscr
        self.stdscr = stdscr
        self.screen_y, self.screen_x = self.stdscr.getmaxyx()
        self.check_size(self.screen_x, self.screen_y)

        # Game zoom for x and y, non negative and non zero
        self.zoom = zoom
        if self.zoom is None:
            self.zoom = Zoom().auto(self.screen_x, self.screen_y)

        # Set arena window
        self.arena_height, self.arena_width = self.screen_y - 2, self.screen_x - 2
        # Note here self.arena_height + 1, without " + 1" occures exception while printing last char in bottom right,
        # because after that cursor moves to the new line of window, so we need one more line to place the cursor.
        self.arena_win = self.stdscr.subwin(self.arena_height + 1, self.arena_width, 1, 1)
        self.arena_win = windows.WinKeysWrapper(self.arena_win)
        # Key bindings
        self.arena_win.bind(settings.KEYS_EXIT, self.game_quit)
        keys_move = (settings.MOVE_UP, settings.MOVE_DOWN, settings.MOVE_LEFT, settings.MOVE_RIGHT)
        self.arena_win.bind(keys_move, self.change_direction)
        self.arena_win.bind(settings.KEYS_NEW_GAME, lambda: self.new(self.zoom))
        self.arena_win.bind(settings.KEYS_PAUSE, self.game_pause)
        self.arena_win.bind(curses.KEY_RESIZE, self.new)
        self.arena_win.bind(settings.KEYS_ZOOM_IN, self.try_zoom_in)
        self.arena_win.bind(settings.KEYS_ZOOM_OUT, lambda: self.new(self.zoom.out()))
        self.arena_win.bind(settings.KEYS_AUTO_ZOOM, self.new)
        self.arena_win.bind(settings.KEYS_REWIND, self.game_rewind)

        # Set bottom menu window
        self.bottom_win = self.stdscr.subwin(1, self.arena_width, self.arena_height + 1, 1)
        attr = curses.has_colors() and curses.color_pair(2)
        self.bottom_win.attrset(attr)
        menu_str = '%s: Quit, %s: New Game, %s: Pause, %s/%s/%s: Zoom in/out/auto, %s: Rewind' % (
            settings.KEYS_EXIT[0],
            settings.KEYS_NEW_GAME[0],
            settings.KEYS_PAUSE[0],
            settings.KEYS_ZOOM_IN[0],
            settings.KEYS_ZOOM_OUT[0],
            settings.KEYS_AUTO_ZOOM[0],
            settings.KEYS_REWIND[0],
        )
        self.bottom_win.addnstr(menu_str, self.arena_width - 1)
        self.bottom_win.noutrefresh()

        # Set top stats window
        self.top_win = self.stdscr.subwin(1, self.arena_width, 0, 1)
        attr = curses.A_BOLD | (curses.has_colors() and curses.color_pair(3))
        self.top_win.attrset(attr)

        # Build arena
        zoomed_width = int(self.arena_width // self.zoom.x)
        zoomed_height = int(self.arena_height // self.zoom.y)
        self.arena = Arena(zoomed_width, zoomed_height)

        # Some initials
        self.init_loop_delay = settings.INIT_DELAY
        self.loop_delay = self.init_loop_delay
        self.time_loop = 0  # For performance testing
        self.key_code = None

    def add_snapshot(self):
        snapshots.append(pickle.dumps(self.arena))

    def get_snapshot(self):
        return pickle.loads(snapshots.pop())

    def game_rewind(self):
        try:
            self.arena = self.get_snapshot()
        except IndexError:
            # No rewinds
            pass
        else:
            self.arena.refresh()
            self.render()
        windows.GameRewindPopup(self.arena_win, message="Rewind mode (%s)\npress 'r'" % len(snapshots)).show()

    def try_zoom_in(self):
        prev_zoom = copy.copy(self.zoom)
        try:
            self.new(self.zoom.in_())
        except TooSmallScreen:
            self.new(prev_zoom)

    def change_direction(self):
        self.arena.direction = self.key_code

    @staticmethod
    def check_size(width, height):
        min_size = 5
        if width < min_size or height < min_size:
            raise TooSmallScreen('Small screen.')

    @staticmethod
    def adjust_curses():
        try:
            curses.curs_set(0)  # Hide cursor
        except curses.error:
            pass

        if curses.has_colors():
            curses.use_default_colors()
            default_bg_color = -1
            curses.init_pair(1, curses.COLOR_BLUE, default_bg_color)
            curses.init_pair(2, curses.COLOR_CYAN, default_bg_color)
            curses.init_pair(3, curses.COLOR_GREEN, default_bg_color)
            curses.init_pair(4, curses.COLOR_MAGENTA, default_bg_color)
            curses.init_pair(5, curses.COLOR_RED, default_bg_color)
            curses.init_pair(6, curses.COLOR_YELLOW, default_bg_color)
            curses.init_pair(7, curses.COLOR_WHITE, default_bg_color)

    def run(self):
        """ Game mainloop """
        while True:
            t1 = time.time()

            # Take snapshot for rewind
            self.add_snapshot()

            # Catch the input and handle it
            self.key_code = self.arena_win.getch()
            self.arena_win.handle_key(self.key_code)

            # Moving snake
            self.arena.snake_go()

            # Render screen
            self.render()

            # Checking gaming rules
            try:
                self.rules()
            except GameOver:
                self.game_over()
            except GameWin:
                self.game_win()

            # Detecting timings
            self.time_loop = time.time() - t1

            # Game delay or game speed
            time.sleep(self.loop_delay)

    def new(self, *args):
        """ Start new game """
        self.stdscr.clear()
        self.stdscr.noutrefresh()
        self.__init__(self.stdscr, *args)

    def rules(self):
        arena = self.arena
        block_under_head = arena.block_under_head
        min_speed = 0.1
        arena.direction = arena.direction or settings.MOVE_RIGHT

        if not any(arena.get_blocks([BlockEfir, BlockFood])):
            raise NoMoreSpace

        self.loop_delay *= 0.99

        if arena.moves_all == 1:
            arena.new_food()

        if block_under_head == BlockFood:
            arena.snake_eat(3)
            arena.new_food()
            self.init_loop_delay *= 0.95
            self.loop_delay = self.init_loop_delay

        if block_under_head == BlockBorder:
            raise BorderException('Hit the border!')

        if block_under_head == BlockSnake:
            raise BodyException('Eat youself!')

        if self.loop_delay < min_speed:
            self.loop_delay = min_speed

    def game_win(self):
        """ Game win screen """
        curses.flash()
        windows.GameWinPopup(self.arena_win).show()

    def game_over(self):
        """ Game over screen """
        curses.flash()
        windows.GameOverPopup(self.arena_win).show()

    def game_quit(self):
        """ Quit game """
        self.arena_win.refresh()
        windows.GameQuitPopup(self.arena_win).show()
        curses.napms(500)
        sys.exit()

    def game_pause(self):
        windows.GamePausePopup(self.arena_win).show()

    def render(self):
        """ Render game """
        self.render_arena()
        self.render_stats()
        curses.doupdate()

    def render_arena(self):
        """ Render arena """
        for block in self.arena:
            for i in range(self.zoom.y):
                for j in range(self.zoom.x):
                    y = block.y * self.zoom.y + i
                    x = block.x * self.zoom.x + j
                    self.arena_win.addstr(y, x, str(block))
                    self.arena_win.chgat(y, x, 1, block.curses_attr)
        self.arena_win.noutrefresh()

    def render_stats(self):
        """ Render stats """
        stats_str = 'Score: %04d | Speed: %03d'
        max_chars = self.arena_width - 1
        stats_str = stats_str % (self.arena.eat_count * 10, 1 / self.loop_delay)
        stats_str = stats_str.rjust(max_chars)
        self.top_win.addnstr(0, 0, stats_str, max_chars)
        self.top_win.noutrefresh()
