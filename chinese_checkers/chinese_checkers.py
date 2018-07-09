import pygame
from pygame.locals import *
from board import *
import sys

class CCheckers():
    def __init__(self, mode = ''):
        pygame.init()
        self.board = Board(mode)
        self.going = False
        
    def loop(self):
        while self.board.going:
            self.board.update()
        print("Game finished.")
        pygame.quit()

    

if __name__ == '__main__':
    if len(sys.argv) == 2:
        mode = sys.argv[1]
        game = CCheckers(mode)
    else:
        game = CCheckers()

    game.loop()