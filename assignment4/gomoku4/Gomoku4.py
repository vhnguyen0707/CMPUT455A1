#!/usr/bin/env python
#/usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY
from simple_board import SimpleGoBoard

import random
import numpy as np

def count_at_depth(node, depth, nodesAtDepth):
    if not node._expanded:
        return
    nodesAtDepth[depth] += 1
    for _, child in node._children.items():
        count_at_depth(child, depth + 1, nodesAtDepth)

class GomokuSimulationPlayer(object):
    def __init__(
        self,
        num_sim,
        size=7,
        exploration=0.4,
    ):
        """
        Player that selects a move based on MCTS from the set of legal moves
        """
        self.name = "Go5"
        self.version = "1.0"
        self.MCTS = MCTS()
        self.num_simulation = num_sim
        self.exploration = exploration
        self.simulation_policy = sim_rule
        self.parent = None

    def reset(self):
        self.MCTS = MCTS()

    def update(self, move):
        self.parent = self.MCTS._root
        self.MCTS.update_with_move(move)

    def get_move(self, board, toplay):
        move = self.MCTS.get_move(
            board,
            toplay,
            num_simulation=self.num_simulation,
            exploration=self.exploration
        )
        self.update(move)
        return move

    def get_node_depth(self, root):
        MAX_DEPTH = 100
        nodesAtDepth = [0] * MAX_DEPTH
        count_at_depth(root, 0, nodesAtDepth)
        prev_nodes = 1
        return nodesAtDepth

    def get_properties(self):
        return dict(version=self.version, name=self.__class__.__name__,)


def run(sim):
    """
    Start the gtp connection and wait for commands.
    """
    board = GoBoard(7)
    con = GtpConnection(
        Go5(num_sim), board
    )
    con.start_connection()


def parse_args():
    """
    Parse the arguments of the program.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--sim",
        type=int,
        default=300,
        help="number of simulations per move, so total playouts=sim*legal_moves",
    )
    args = parser.parse_args()

    num_sim = args.sim

    return num_sim


if __name__ == "__main__":
    num_sim = parse_args()
    run(num_sim)
