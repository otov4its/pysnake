import curses
from .game import Game


def go(stdscr):
    Game(stdscr).run()  # Start game


def main():
    # Curses convinient wrapper
    curses.wrapper(go)


if __name__ == '__main__':
    main()