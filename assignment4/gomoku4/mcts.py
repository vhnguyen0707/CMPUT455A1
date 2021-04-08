#import os, sys
import numpy as np

from board_util import GoBoardUtil, BLACK, WHITE, PASS
from gtp_connection import point_to_coord, format_point

PASS = "pass"

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
        pattern = board.get_pattern_moves()
        if pattern is None:
            moves = board.get_empty_points()
        else:
            _, moves = pattern
        for move in moves:
            self._children[move] = TreeNode(self)
            self._children[move]._move = move
        #self._children[PASS] = TreeNode(self)
        #self._children[PASS]._move = PASS
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