#!/usr/bin/env python
#/usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY
from simple_board import SimpleGoBoard

import math
import numpy as np

from mcts import MCTS

class GomokuSimulationPlayer(object):

    def __init__(self, board_size=7):
        self.board_size = board_size
        self.exploration = math.sqrt(2)
        self.name="Gomoku4"
        self.version = 4.0
     
    def get_move(self, board, color_to_play):
        mcts = MCTS()
        return mcts.get_move(board, color_to_play, self.exploration)

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(GomokuSimulationPlayer(), board)
    con.start_connection()

if __name__=='__main__':
    run()
