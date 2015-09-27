"""
Game exceptions
"""


class PySnakeException(Exception):
    """Base game exception"""
    pass


class GameOver(PySnakeException):
    pass


class GameWin(PySnakeException):
    pass


class TooSmallScreen(PySnakeException):
    pass


class BorderException(GameOver):
    pass


class BodyException(GameOver):
    pass


class NoMoreSpace(GameWin):
    pass
