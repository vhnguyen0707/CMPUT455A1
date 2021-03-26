"""
board.py

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from board_util import (
    GoBoardUtil,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    PASS,
    is_black_white,
    is_black_white_empty,
    coord_to_point,
    where1d,
    MAXSIZE,
    GO_POINT
)
import math

"""
The GoBoard class implements a board and basic functions to play
moves, check the end of the game, and count the acore at the end.
The class also contains basic utility functions for writing a Go player.
For many more utility functions, see the GoBoardUtil class in board_util.py.

The board is stored as a one-dimensional array of GO_POINT in self.board.
See GoBoardUtil.coord_to_point for explanations of the array encoding.
"""
class GoBoard(object):
    def __init__(self, size):
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)
        self.calculate_rows_cols_diags()
        self.generate_pattern()

    def calculate_rows_cols_diags(self):
        if self.size < 5:
            return
        # precalculate all rows, cols, and diags for 5-in-a-row detection
        self.rows = []
        self.cols = []
        for i in range(1, self.size + 1):
            current_row = []
            start = self.row_start(i)
            for pt in range(start, start + self.size):
                current_row.append(pt)
            self.rows.append(current_row)
            
            start = self.row_start(1) + i - 1
            current_col = []
            for pt in range(start, self.row_start(self.size) + i, self.NS):
                current_col.append(pt)
            self.cols.append(current_col)
        
        self.diags = []
        # diag towards SE, starting from first row (1,1) moving right to (1,n)
        start = self.row_start(1)
        for i in range(start, start + self.size):
            diag_SE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            if len(diag_SE) >= 5:
                self.diags.append(diag_SE)
        # diag towards SE and NE, starting from (2,1) downwards to (n,1)
        for i in range(start + self.NS, self.row_start(self.size) + 1, self.NS):
            diag_SE = []
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_SE) >= 5:
                self.diags.append(diag_SE)
            if len(diag_NE) >= 5:
                self.diags.append(diag_NE)
        # diag towards NE, starting from (n,2) moving right to (n,n)
        start = self.row_start(self.size) + 1
        for i in range(start, start + self.size):
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_NE) >=5:
                self.diags.append(diag_NE)
        assert len(self.rows) == self.size
        assert len(self.cols) == self.size
        assert len(self.diags) == (2 * (self.size - 5) + 1) * 2

    def reset(self, size):
        """
        Creates a start state, an empty board with given size.
        """
        self.size = size
        self.NS = size + 1
        self.WE = 1
        self.ko_recapture = None
        self.last_move = None
        self.last2_move = None
        self.current_player = BLACK
        self.maxpoint = size * size + 3 * (size + 1)
        self.board = np.full(self.maxpoint, BORDER, dtype=GO_POINT)
        self._initialize_empty_points(self.board)
        self.calculate_rows_cols_diags()

    def copy(self):
        b = GoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.last_move = self.last_move
        b.last2_move = self.last2_move
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def get_color(self, point):
        return self.board[point]

    def pt(self, row, col):
        return coord_to_point(row, col, self.size)

    def is_legal(self, point, color):
        """
        Check whether it is legal for color to play on point
        This method tries to play the move on a temporary copy of the board.
        This prevents the board from being modified by the move
        """
        board_copy = self.copy()
        can_play_move = board_copy.play_move(point, color)
        return can_play_move

    def get_empty_points(self):
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)
    
    def get_color_points(self, color):
        """
        Return:
            All points of color on the board
        """
        return where1d(self.board == color)

    def row_start(self, row):
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1

    def _initialize_empty_points(self, board):
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start = self.row_start(row)
            board[start : start + self.size] = EMPTY

    def is_eye(self, point, color):
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = GoBoardUtil.opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge  # 0 at edge, 1 in center

    def _is_surrounded(self, point, color):
        """
        check whether empty point is surrounded by stones of color
        (or BORDER) neighbors
        """
        for nb in self._neighbors(point):
            nb_color = self.board[nb]
            if nb_color != BORDER and nb_color != color:
                return False
        return True

    def _has_liberty(self, block):
        """
        Check if the given block has any liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            empty_nbs = self.neighbors_of_color(stone, EMPTY)
            if empty_nbs:
                return True
        return False

    def _block_of(self, stone):
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        color = self.get_color(stone)
        assert is_black_white(color)
        return self.connected_component(stone)

    def connected_component(self, point):
        """
        Find the connected component of the given point.
        """
        marker = np.full(self.maxpoint, False, dtype=bool)
        pointstack = [point]
        color = self.get_color(point)
        assert is_black_white_empty(color)
        marker[point] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _detect_and_process_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
        and returns None otherwise.
        This result is used in play_move to check for possible ko
        """
        single_capture = None
        opp_block = self._block_of(nb_point)
        if not self._has_liberty(opp_block):
            captures = list(where1d(opp_block))
            self.board[captures] = EMPTY
            if len(captures) == 1:
                single_capture = nb_point
        return single_capture

    def play_move(self, point, color):
        """
        Play a move of color on point
        Returns boolean: whether move was legal
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            self.ko_recapture = None
            self.current_player = GoBoardUtil.opponent(color)
            self.last2_move = self.last_move
            self.last_move = point
            return True
        elif self.board[point] != EMPTY:
            return False
        # if point == self.ko_recapture:
        #     return False

        # General case: deal with captures, suicide, and next ko point
        # opp_color = GoBoardUtil.opponent(color)
        # in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        # single_captures = []
        # neighbors = self._neighbors(point)
        # for nb in neighbors:
        #     if self.board[nb] == opp_color:
        #         single_capture = self._detect_and_process_capture(nb)
        #         if single_capture != None:
        #             single_captures.append(single_capture)
        # block = self._block_of(point)
        # if not self._has_liberty(block):  # undo suicide move
        #     self.board[point] = EMPTY
        #     return False
        # self.ko_recapture = None
        # if in_enemy_eye and len(single_captures) == 1:
        #     self.ko_recapture = single_captures[0]
        self.current_player = GoBoardUtil.opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        return True

    def neighbors_of_color(self, point, color):
        """ List of neighbors of point of given color """
        nbc = []
        for nb in self._neighbors(point):
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def _neighbors(self, point):
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point):
        """ List of all four diagonal neighbors of point """
        return [
            point - self.NS - 1,
            point - self.NS + 1,
            point + self.NS - 1,
            point + self.NS + 1,
        ]

    def last_board_moves(self):
        """
        Get the list of last_move and second last move.
        Only include moves on the board (not None, not PASS).
        """
        board_moves = []
        if self.last_move != None and self.last_move != PASS:
            board_moves.append(self.last_move)
        if self.last2_move != None and self.last2_move != PASS:
            board_moves.append(self.last2_move)
            return 

    def detect_five_in_a_row(self):
        """
        Returns BLACK or WHITE if any five in a row is detected for the color
        EMPTY otherwise.
        """
        for r in self.rows:
            result = self.has_five_in_list(r)
            if result != EMPTY:
                return result
        for c in self.cols:
            result = self.has_five_in_list(c)
            if result != EMPTY:
                return result
        for d in self.diags:
            result = self.has_five_in_list(d)
            if result != EMPTY:
                return result
        return EMPTY

    def has_five_in_list(self, list):
        """
        Returns BLACK or WHITE if any five in a rows exist in the list.
        EMPTY otherwise.
        """
        prev = BORDER
        counter = 1
        for stone in list:
            if self.get_color(stone) == prev:
                counter += 1
            else:
                counter = 1
                prev = self.get_color(stone)
            if counter == 5 and prev != EMPTY:
                return prev
        return EMPTY


    #================ A3 ===================
    def generate_pattern(self):
        # win pattern:
        b_win = np.array([BLACK,BLACK,BLACK,BLACK,BLACK], dtype=GO_POINT)
        w_win = 3 - b_win
        win = np.array([b_win, w_win])
        #print("win pattern:\n", win)
        #print(type(win[0,0]))

        # blockwin pattern:
        b_blockwin = np.array([[BLACK,WHITE,WHITE,WHITE,WHITE], [WHITE,BLACK,WHITE,WHITE,WHITE],
                                [WHITE,WHITE,BLACK,WHITE,WHITE], [WHITE,WHITE,WHITE,BLACK,WHITE],
                                [WHITE,WHITE,WHITE,WHITE,BLACK]
                            ], dtype=GO_POINT)
        w_blockwin = 3 - b_blockwin
        blockwin = np.array([b_blockwin, w_blockwin])
        #print("blockwin pattern:\n", blockwin)

        # openfour pattern:
        b_open4 = np.array([EMPTY,BLACK,BLACK,BLACK,BLACK,EMPTY], dtype=GO_POINT)
        w_open4 = 3 - b_open4
        w_open4[w_open4 == 3] = EMPTY
        open4 = np.array([b_open4, w_open4])
        #print("openfour pattern:\n", open4)

        # blockopenfour pattern:
        b_blockopen4 = np.array([[EMPTY,BLACK,WHITE,WHITE,WHITE,EMPTY], [EMPTY,WHITE,WHITE,WHITE,BLACK,EMPTY],
                                  [BLACK,WHITE,WHITE,EMPTY,WHITE,EMPTY], [EMPTY,WHITE,WHITE,BLACK,WHITE,EMPTY], 
                                  [EMPTY,WHITE,WHITE,EMPTY,WHITE,BLACK], [BLACK,WHITE,EMPTY,WHITE,WHITE,EMPTY],
                                  [EMPTY,WHITE,BLACK,WHITE,WHITE,EMPTY], [EMPTY,WHITE,EMPTY,WHITE,WHITE,BLACK],
                                  [BLACK,EMPTY,WHITE,WHITE,WHITE,BLACK], [BLACK,WHITE,WHITE,WHITE,EMPTY,EMPTY],
                                  [EMPTY,EMPTY,WHITE,WHITE,WHITE,BLACK], [EMPTY,WHITE,WHITE,WHITE,EMPTY,BLACK],
                                  [BLACK,EMPTY,WHITE,WHITE,WHITE,EMPTY]
                                ], dtype=GO_POINT)

        not_b_blockopen4 = np.array([[EMPTY,EMPTY,WHITE,WHITE,WHITE,EMPTY,BLACK],[BLACK,EMPTY,WHITE,WHITE,WHITE,EMPTY,EMPTY]], dtype=GO_POINT)

        b_blockopen4_more = np.array([BLACK,EMPTY,WHITE,WHITE,WHITE,EMPTY,BLACK], dtype=GO_POINT) # case: x.ooo.x

        w_blockopen4 = 3 - b_blockopen4
        w_blockopen4[w_blockopen4 == 3] = EMPTY

        not_w_blockopen4 = 3 - not_b_blockopen4
        not_w_blockopen4[not_w_blockopen4 == 3] = EMPTY
        
        w_blockopen4_more = 3 - b_blockopen4_more
        w_blockopen4_more[w_blockopen4_more == 3] = EMPTY

        blockopen4 = np.array([b_blockopen4, w_blockopen4, b_blockopen4_more, w_blockopen4_more])
        #print("blockopenfour pattern:\n", blockopen4)
        not_blockopen4 = np.array([not_b_blockopen4, not_w_blockopen4])

        self.pattern = np.array([win, blockwin, open4, blockopen4])

        return self.pattern, not_blockopen4

    
    def get_nlines_contain_point(self, point, n_in_row):
        n = n_in_row - 1

        board2d = GoBoardUtil.get_twoD_board(self)

        # index padded 1D to 2D
        r = point // self.NS - 1
        c = point % self.NS - 1
        
        # NS:
        N = max(r - n, 0)
        S = min(r + n, self.size - 1)
        col = board2d[N:(S+1), c]

        # WE:
        W = max(c - n, 0)
        E = min(c + n, self.size - 1)
        row = board2d[r,W:(E+1)]

        # NW -> SE:
        diag1 = []

        NW = min(r, c, n)
        SE = min(self.size - 1 - r, self.size - 1 - c, n)

        for i in range(-NW,SE+1):
            diag1.append(board2d[r+i,c+i])
            #print("diag1: ", (r+i,c+i))

        # NE -> SW:
        diag2 = []
        
        NE = min(r,self.size - 1 - c, n)
        SW = min(self.size - 1 - r, c, n)
        
        for i in range(-NE,SW+1):
            diag2.append(board2d[r+i,c-i])
            #print("diag2: ", (r+i,c-i))

        diag1 = np.array(diag1, dtype=GO_POINT)
        diag2 = np.array(diag2, dtype=GO_POINT)

        if len(row) < n_in_row:
            row = np.empty(shape = (0, 0))
        if len(col) < n_in_row:
            col = np.empty(shape = (0, 0))
        if len(diag1) < n_in_row:
            diag1 = np.empty(shape = (0, 0))
        if len(diag2) < n_in_row:
            diag2 = np.empty(shape = (0, 0))

        return [row, col, diag1, diag2]

    def undo_move(self, move):
        self.board[move] = EMPTY
        self.current_player = GoBoardUtil.opponent(self.current_player)

    def check_who_wins(self):
        '''
        check if the game is end by checnking no empty position or finding 5-in-row in WHITE or BLACK
        '''
        #return ( len(self.get_empty_points()) < 1 or self.detect_five_in_a_row() != EMPTY )
        if self.detect_five_in_a_row() == WHITE :
            return WHITE
        elif self.detect_five_in_a_row() == BLACK :
            return BLACK
        else:
            return False 

    def check_policy_moves(self):
        # get a list of all legal moves on the board for current color 
        legal_moves = GoBoardUtil.generate_legal_moves(self, self.current_player)

        win_moves = []
        block_win_moves = []
        open_four_moves = []
        block_open_four_moves = []

        pattern_list, not_block_open_four_pattern = self.generate_pattern()
        block_win_pattern = pattern_list[1]
        open_four_pattern = pattern_list[2]
        block_open_four_pattern = pattern_list[3] # has four lists


        # check if moves will be one of the lists above
        for move in legal_moves: 

            self.play_move(move,self.current_player)
            color = GoBoardUtil.opponent(self.current_player)
            win = self.win(color,move,win_moves)
            if (not win):
                block_win = self.block_win(color,move,block_win_moves,block_win_pattern)
                if (not block_win):
                    open_four = self.open_four(color,move,open_four_moves,open_four_pattern)
                    if (not open_four):
                        block_open_four = self.block_open_four(color,move,block_open_four_moves,block_open_four_pattern,not_block_open_four_pattern)
                        # block_open_four_more = self.block_open_four_more(move,board_copy,block_open_four_moves,block_open_four_pattern, not_block_open_four_pattern)
            self.undo_move(move)

        if win_moves:
            move_type = "Win"
            move_list = win_moves

        elif block_win_moves:
            move_type = "BlockWin"
            move_list = block_win_moves
        
        elif open_four_moves:
            move_type = "OpenFour"
            move_list = open_four_moves

        elif block_open_four_moves:
            move_type = "BlockOpenFour"
            move_list = block_open_four_moves

        else:
            move_type = "Random"
            move_list = legal_moves
            
        return move_type, move_list

    # check if win
    def win(self,color,move,win_moves):
        winner = self.check_who_wins()
        if color == winner: 
            win_moves.append(move)
            return True
        return False

    # check if block_win
    def block_win(self,color,move,block_win_moves,block_win_pattern):
        # get the four (row, col, diag1, diag2) lines after playing the move on board
        lines_list = self.get_nlines_contain_point(move, 5)
        if color == BLACK:
            current_block_win_pattern = block_win_pattern[0]
        else:
            current_block_win_pattern = block_win_pattern[1]
        for pattern in current_block_win_pattern: 
            # for each row, col, diag1, diag2
            for line in lines_list:
                # if line matches the one of the pattern, then block_win is True
                if line.size:
                    for i in range(0, len(line) - 5 + 1):
                        part_line = line[i:i+5] 
                        '''print("block_win")
                        print(line)
                        print(part_line)
                        print(pattern)'''
                        if np.allclose(part_line, pattern):
                            block_win_moves.append(move)
                            return True     
        return False

    # check if open_four
    def open_four(self,color,move,open_four_moves,open_four_pattern):
        # get the four (row, col, diag1, diag2) lines after playing the move on board
        lines_list = self.get_nlines_contain_point(move, 6)
        if color == BLACK:
            # only one pattern
            current_open_four_pattern = open_four_pattern[0]
        else:
            current_open_four_pattern = open_four_pattern[1]
            # for each row, col, diag1, diag2
        for line in lines_list:
            # if line matches the one of the pattern, then block_win is True
            if line.size:
                for i in range(0, len(line) - 6 + 1):
                    part_line = line[i:i+6] 
                    '''print("open_four")
                    print(line)
                    print(part_line)
                    print(b_open_four_pattern)'''
                    if np.allclose(part_line, current_open_four_pattern):
                        open_four_moves.append(move)
                        return True
        return False

    # check if block_open_four
    def block_open_four(self,color,move,block_open_four_moves,block_open_four_pattern,not_block_open_four_pattern): 

        b_spe1 = np.array([EMPTY,WHITE,WHITE,WHITE,EMPTY,BLACK],dtype=GO_POINT)
        b_spe2 = np.array([BLACK,EMPTY,WHITE,WHITE,WHITE,EMPTY],dtype=GO_POINT)
        w_spe1 = 3 - b_spe1
        w_spe1[w_spe1 == 3] = EMPTY
        w_spe2 = 3 - b_spe2
        w_spe2[w_spe2 == 3] = EMPTY

        # get the four (row, col, diag1, diag2) lines after playing the move on board
        lines_list = self.get_nlines_contain_point(move, 6)
        if color == BLACK:
            current_block_open_four_pattern = block_open_four_pattern[0]
        else:
            current_block_open_four_pattern = block_open_four_pattern[1]
            for pattern in current_block_open_four_pattern: 
                # for each row, col, diag1, diag2
                for line in lines_list:
                    # if line matches the one of the pattern, then block_win is True
                    if line.size:
                        for i in range(0, len(line) - 6 + 1):
                            part_line = line[i:i+6] 
                            '''print("block_open_four")
                            print(part_line)
                            print(pattern)'''
                            if np.allclose(part_line, pattern):
                                # special case [EMPTY,WHITE,WHITE,WHITE,EMPTY,BLACK],[BLACK,EMPTY,WHITE,WHITE,WHITE,EMPTY]
                                if np.allclose(pattern, b_spe1) or np.allclose(pattern, b_spe2) or np.allclose(pattern, w_spe1) or np.allclose(pattern, w_spe2):
                                    if self.size > 6:
                                        block_open_four_more = self.block_open_four_more(color,move,block_open_four_moves,block_open_four_pattern,not_block_open_four_pattern)
                                        if block_open_four_more:
                                            block_open_four_moves.append(move)
                                            return True
                                        else:
                                            return False
                                block_open_four_moves.append(move)
                                return True
        return False

    # more
    def block_open_four_more(self,color,move,block_open_four_moves,block_open_four_pattern,not_block_open_four_pattern):
        lines_list = self.get_nlines_contain_point(move, 7)
        if color == BLACK:
            current_block_open_four_pattern = block_open_four_pattern[2]
            current_not_block_open_four_pattern = not_block_open_four_pattern[0]
        else:
            current_block_open_four_pattern = block_open_four_pattern[3]
            current_not_block_open_four_pattern = not_block_open_four_pattern[1]
        # for each row, col, diag1, diag2
        for line in lines_list:
            # if line matches the one of the pattern, then block_win is True
            if line.size:
                for i in range(0, len(line) - 7 + 1):
                    part_line = line[i:i+7] 
                    '''print(part_line)
                    print(block_open_four_pattern)'''
                    if np.allclose(part_line, current_block_open_four_pattern):
                        block_open_four_moves.append(move)
                        return True
                    else:
                        for pattern in current_not_block_open_four_pattern: 
                            if np.allclose(part_line, pattern):
                                return False
        return True

        
        
            


        
        