import numpy as np

from board_util import GoBoardUtil, BLACK, WHITE, EMPTY

import signal
import random

TIMELIMIT = 59

def handler(signum, frame):
    raise Exception()

signal.signal(signal.SIGALRM, handler)

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

    def winrate(self, max_flag):
        if self._n_visits == 0:
            return 0
        
        if max_flag:
            return float(self._black_wins / self._n_visits)
        else:
            return float((self._n_visits - self._black_wins) / self._n_visits)

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

    def _evaluate_rollout(self, board, toplay):
        winner = self.get_result(board)

        while winner is None and len(board.get_empty_points()) > 0:
            
            if len(board.get_empty_points()) <= 5:
                winner, _ = board.solve()
                break
            
            legal_moves = filtered_moves(board)
            move = random.choice(legal_moves)
            board.play_move_gomoku(move, board.current_player)
            winner = self.get_result(board)
        
        if winner == BLACK or winner == 'b':
            return 1
        elif winner == 'draw':
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
        signal.alarm(TIMELIMIT)

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
            max_flag = toplay == BLACK

            moves_ls = [
                (move, node._n_visits, node.winrate(max_flag)) for move, node in self._root._children.items()
            ]

            _, max_visit, _ = max(moves_ls, key=lambda i: i[1])
            max_visit_moves = [move for move in moves_ls if move[1] == max_visit]
            move = max(max_visit_moves, key=lambda i: i[2])
            
            return move[0]
