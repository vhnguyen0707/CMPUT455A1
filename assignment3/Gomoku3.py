#!/usr/local/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY, PASS
from board import GoBoard
import numpy as np
import random

class Gomoku():
    def __init__(self):
        """
        Gomoku player that selects moves randomly from the set of legal moves.
        Passes/resigns only at the end of the game.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "GomokuAssignment3"
        self.version = 1.0
        self.numSimulations = 10


    def get_move(self, board, color, policy_type):
        """
        Run one-ply MC simulations to get a move to play.
        """
        if policy_type == "rule_based":
            _, moves = board.check_policy_moves()
        else:
            moves = board.get_empty_points()
        
        if len(moves) < 1:
            return None

        moveWins = [] 

        for move in moves:
            cboard = board.copy()
            wins = self.simulateMove(cboard, move, color, policy_type)
            moveWins.append(wins)

        #Select best move
        max_child = np.argmax(moveWins)
        return moves[max_child]

    def simulateMove(self, board, move, toPlay, policy_type):
        """
        Run simulations for a given move
        """
        wins = 0
        for _ in range(self.numSimulations):
            result = self.simulate(board, move, toPlay, policy_type)
            if result == toPlay:
                wins += 1
        return wins

    def simulate(self, board, move, toPlay, policy_type):
        """
        Run a simulated game for a given move
        """
        board.play_move(move, toPlay)
        opp = GoBoardUtil.opponent(toPlay)
        passes = 0
       
        while board.detect_five_in_a_row() == EMPTY and len(board.get_empty_points()) != 0:
            color = board.current_player
            if policy_type == "rule_based":
                _, moves = board.check_policy_moves()
            else:
                moves = board.get_empty_points()
            move = random.choice(moves)
            board.play_move(move, color)
            
            if move == PASS:
                passes += 1
            else:
                passes = 0
            if passes >= 2:
                break
        return board.detect_five_in_a_row()


def run():
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(Gomoku(), board)
    con.start_connection()


if __name__ == "__main__":
    run()
