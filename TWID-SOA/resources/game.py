from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625
from board import Board
from cards import Cards
from shortuuid import ShortUUID

class Game(metaclass=MultipleMeta):
    def __init__(self):
        self.board = Board()
        self.cards = Cards()
        self.id = ShortUUID().random(length=10) # https://stackoverflow.com/questions/24796654/python-uuid4-how-to-limit-the-length-of-unique-chars

    def __init__(self, id: str):
        self.board = Board()
        self.cards = Cards()
        self.id = id

    def __repr__(self):
        return self.id