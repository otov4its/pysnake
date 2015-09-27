"""
Game settings
"""

import curses


# Initial game delay (aka game speed)
INIT_DELAY = 0.5  # Seconds

# Control keys
MOVE_UP = curses.KEY_UP
MOVE_DOWN = curses.KEY_DOWN
MOVE_LEFT = curses.KEY_LEFT
MOVE_RIGHT = curses.KEY_RIGHT
KEYS_EXIT = 'qQ'
KEYS_NEW_GAME = 'nN'
KEYS_ZOOM_IN = '+'
KEYS_ZOOM_OUT = '-'
KEYS_AUTO_ZOOM = 'aA'
KEYS_PAUSE = 'pP'
KEYS_REWIND = 'rR'

# Graphics
ARENA_SNAKE = 'O'
ARENA_FOOD = '@'
ARENA_EFIR = ' '
ARENA_BRICK = '#'

# Zoom factor (one terminal character's height/width ratio)
# for pseudo square terminal screen
ZOOM_FACTOR = 15 / 8.0
