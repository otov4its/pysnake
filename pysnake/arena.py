from collections import deque
import random
import curses
import copy

from .exeptions import TooSmallScreen
from . import settings


class Arena(object):
    """
    Encapsulates Snake Game's arena structure
    """
    def __init__(self, width, height):
        """Create a new Arena instance"""
        # Arena size
        self.width = width
        self.height = height
        min_size = 3
        if self.width < min_size or self.height < min_size:
            raise TooSmallScreen('Small arena size.')

        # Inits
        self.touched_blocks = []  # Touched blocks since last render
        self.moves_all = 0
        self.moves_from_eat = 0
        self.eat_count = 0
        self.direction = None
        self.prev_direction = None
        self.block_under_head = None
        self.last_snake_tail = None
        self.misdirection = [
            (settings.MOVE_UP, settings.MOVE_DOWN),
            (settings.MOVE_DOWN, settings.MOVE_UP),
            (settings.MOVE_LEFT, settings.MOVE_RIGHT),
            (settings.MOVE_RIGHT, settings.MOVE_LEFT)
        ]  # Prevent occasional "game over" when pressing reverse direction keys

        # Build arena as dictionary with keys (x, y)
        self.arena = {}
        for y in range(self.height):
            for x in range(self.width):
                    self.set_block(BlockEfir(x, y))  # Fill arena with empty blocks

        # Draw the arena's border
        self.set_border()

        # Init snake
        # Snake's body is the python deque object
        # See https://docs.python.org/3.4/library/collections.html#collections.deque
        self.snake_body = deque(maxlen=1)
        head = BlockSnake(self.width // 2, self.height // 2)
        self.snake_body.append(head)
        self.set_block(head)

    def __iter__(self):
        """Yields only touched blocks"""
        for block in self.touched_blocks:
            yield block
        self.touched_blocks = []

    def set_block(self, block):
        """Set arena block"""
        self.arena[block.x, block.y] = block
        self.touched_blocks.append(block)

    def get_block(self, x, y):
        """Get arena block"""
        return self.arena[x, y]

    def get_blocks(self, which):
        """Get all blocks of the specified type"""
        blocks = filter(lambda bl: any([bl == block for block in which]), self.arena.values())
        return blocks

    def set_border(self):
        """Draw arena's border"""
        for x in range(self.width):  # Horizontal borders
            self.set_block(BlockBorder(x, 0))
            self.set_block(BlockBorder(x, self.height - 1))
        for y in range(self.height):  # Vertical borders
            self.set_block(BlockBorder(0, y))
            self.set_block(BlockBorder(self.width - 1, y))

    def new_food(self, num=1):
        """Generate food in random empty block"""
        # Get all empty blocks
        blocks_efir = list(self.get_blocks([BlockEfir]))
        # Randomize blocks
        random.shuffle(blocks_efir)
        for block in blocks_efir[:num]:
            self.set_block(BlockFood(block.x, block.y))

    def refresh(self):
        """Touch all the blocks of arena"""
        self.touched_blocks = []
        all_blocks = self.arena.values()
        self.touched_blocks.extend(all_blocks)

    @property
    def snake_length(self):
        return len(self.snake_body)

    @property
    def snake_head(self):
        return self.snake_body[-1]  # Head in end of deque

    @property
    def snake_tail(self):
        return self.snake_body[0]  # Tail in begining of deque

    def snake_grow(self, delta=1):
        """Snake grows"""
        new_length = self.snake_body.maxlen + delta
        self.snake_body = deque(self.snake_body, new_length)
        # Fill new body
        self.snake_body.extendleft([None] * delta)

    def snake_eat(self, count=1):
        """Snake eats"""
        self.snake_grow(count)  # Snake grows
        # Update stats
        self.moves_from_eat = 0
        self.eat_count += 1

    def snake_go(self):
        """Driving of snake"""
        self.last_snake_tail = self.snake_tail

        # Prevent misdirection
        if self.snake_length > 1:
            if (self.prev_direction, self.direction) in self.misdirection:
                self.direction = self.prev_direction
        self.prev_direction = self.direction

        # Cloning head
        head = self.snake_head.clone()

        # Move head
        if self.direction == settings.MOVE_UP:
            head.y -= 1  # Go up
        elif self.direction == settings.MOVE_DOWN:
            head.y += 1  # Go down
        elif self.direction == settings.MOVE_RIGHT:
            head.x += 1  # Go right
        elif self.direction == settings.MOVE_LEFT:
            head.x -= 1  # Go left

        # Append new head to body
        self.snake_body.append(head)

        # Amend snake's blocks (erase tail and set new head)
        if self.last_snake_tail:
            self.set_block(BlockEfir(self.last_snake_tail.x, self.last_snake_tail.y))
        self.block_under_head = self.get_block(self.snake_head.x, self.snake_head.y)
        self.set_block(BlockSnake(self.snake_head.x, self.snake_head.y))

        # Update stats
        self.moves_all += 1
        self.moves_from_eat += 1


class Block(object):
    """
    Base class for blocks of arena
    """
    kind = ''  # Block type
    curses_attr = 0  # Curses attributes

    def __init__(self, x, y):
        """
        Create new block with given co-ordinates
        """
        self.x = x
        self.y = y

    def __str__(self):
        return self.kind

    def __eq__(self, other):
        return isinstance(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def clone(self):
        """Clone yourself"""
        return copy.copy(self)


class BlockEfir(Block):
    """Representative of empty arena space"""
    kind = settings.ARENA_EFIR


class BlockSnake(Block):
    """Snake's body block"""
    kind = settings.ARENA_SNAKE


class BlockBorder(Block):
    """Arena's border block"""
    kind = settings.ARENA_BRICK


class BlockFood(Block):
    """Arena's food block"""
    kind = settings.ARENA_FOOD

    def __init__(self, x, y):
        """
        Create new block with random color
        """
        super(BlockFood, self).__init__(x, y)
        if curses.has_colors():
            self.curses_attr |= curses.color_pair(random.randrange(1, 7))
