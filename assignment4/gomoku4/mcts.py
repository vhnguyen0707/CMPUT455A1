import os, sys
import numpy as np

from board_util import GoBoardUtil, BLACK, WHITE, PASS, EMPTY
from gtp_connection import point_to_coord, format_point

import signal
import random

def handler(signum, frame):
    raise Exception()

signal.signal(signal.SIGALRM, handler)

#PASS = "pass"
TIMELIMIT = 60

def filtered_moves(board):
    pattern = board.get_pattern_moves()
    if pattern is None:
        moves = board.get_empty_points()
        np.random.shuffle(moves)
        return moves
    else:
        return pattern[1]

def uct_val(node, child, exploration, max_flag):
    if child._n_visits == 0:
        return float("inf")
    if max_flag:
        return float(child._black_wins) / child._n_visits + exploration * np.sqrt(
            np.log(node._n_visits) / child._n_visits
        )
    else:
        return float(
            child._n_visits - child._black_wins
        ) / child._n_visits + exploration * np.sqrt(
            np.log(node._n_visits) / child._n_visits
        )


class TreeNode(object):
    """
    A node in the MCTS tree.
    """

    version = 0.22
    name = "MCTS Player"

    def __init__(self, parent):
        """
        parent is set when a node gets expanded
        """
        self._parent = parent
        self._children = {}  # a map from move to TreeNode
        self._n_visits = 0
        self._black_wins = 0
        self._expanded = False
        self._move = None

    def expand(self, board, color):
        """
        Expands tree by creating new children.
        """
        moves = filtered_moves(board)
        for move in moves:
            self._children[move] = TreeNode(self)
            self._children[move]._move = move
        self._expanded = True

    def select(self, exploration, max_flag):
        """
        Select move among children that gives maximizes UCT. 
        If number of visits are zero for a node, value for that node is infinite, so definitely will get selected

        It uses: argmax(child_num_black_wins/child_num_vists + C * sqrt(2 * ln * Parent_num_vists/child_num_visits) )
        Returns:
        A tuple of (move, next_node)
        """
        return max(
            self._children.items(),
            key=lambda items: uct_val(self, items[1], exploration, max_flag),
        )

    def update(self, leaf_value):
        """
        Update node values from leaf evaluation.
        Arguments:
        leaf_value -- the value of subtree evaluation from the current player's perspective.
        
        Returns:
        None
        """
        self._black_wins += leaf_value
        self._n_visits += 1

    def update_recursive(self, leaf_value):
        """
        Like a call to update(), but applied recursively for all ancestors.

        Note: it is important that this happens from the root downward so that 'parent' visit
        counts are correct.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.update_recursive(leaf_value)
        self.update(leaf_value)

    def is_leaf(self):
        """
        Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def is_root(self):
        return self._parent is None

class MCTS(object):
    def __init__(self):

        self._root = TreeNode(None)
        self.toplay = BLACK

    def _playout(self, board, color):
        print("playout")
        node = self._root
        if not node._expanded:
            node.expand(board, color)
        while not node.is_leaf():
            max_flag = color == BLACK
            move, next_node = node.select(self.exploration, max_flag)
            
            board.play_move_gomoku(move, color)
            color = GoBoardUtil.opponent(color)
            node = next_node
        assert node.is_leaf()
        if not node._expanded:
            node.expand(board, color)

        assert board.current_player == color
        leaf_value = self._evaluate_rollout(board, color)
        node.update_recursive(leaf_value)
        print("backpropagation")

    def _evaluate_rollout(self, board, toplay):
        print("simulation")
        winner = self.get_result(board)

        while winner is None and len(board.get_empty_points()) > 0:
            legal_moves = filtered_moves(board)
            move = random.choice(legal_moves)
            board.play_move_gomoku(move, board.current_player)
            winner = self.get_result(board)
        
        print("winner: ", winner)
        if winner == BLACK:
            return 1
        elif winner == EMPTY:
            return 0.5
        else:
            return 0

    def get_result(self, board):
        game_end, winner = board.check_game_end_gomoku()
        if game_end:
            return winner
        if len(board.get_empty_points()) == 0:
            return 'draw'
        return None
    
    def get_move(
        self,
        board,
        toplay,
        exploration,
    ):  
        signal.alarm(TIMELIMIT - 1)

        try: 
            if self.toplay != toplay:
                self._root = TreeNode(None)
            self.toplay = toplay
            self.exploration = exploration
            while True:
                board_copy = board.copy()
                self._playout(board_copy, toplay)
            signal.alarm(0)
        
        except Exception:
            moves_ls = [
                (move, node._n_visits) for move, node in self._root._children.items()
            ]

            moves_ls = sorted(moves_ls, key=lambda i: i[1], reverse=True)
            print(moves_ls)
            move = moves_ls[0]
        
            return move[0]

    def update_with_move(self, last_move):
        """
        Step forward in the tree, keeping everything we already know about the subtree, assuming
        that get_move() has been called already. Siblings of the new root will be garbage-collected.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
        else:
            self._root = TreeNode(None)
        self._root._parent = None
        self.toplay = GoBoardUtil.opponent(self.toplay)