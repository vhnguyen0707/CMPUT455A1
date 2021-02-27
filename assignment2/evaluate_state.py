from board_util import (
    BLACK,
    WHITE
)

VALUE_SCHEME = [0, 1, 2, 4, 12, 1000000000]

def get_line_point(state, line):
    count_black = 0
    count_white = 0

    for cell in line:
        cell_color = state.board[cell]

        if cell_color == BLACK:
            count_black += 1
        elif cell_color == WHITE:
            count_white += 1

    if count_black >= 1 and count_white >= 1:
        return 0

    if state.current_player == BLACK:
        return VALUE_SCHEME[count_black] - VALUE_SCHEME[count_white]
    else:
        return VALUE_SCHEME[count_white] - VALUE_SCHEME[count_black]

def evaluate_state_forToPlay(state):
    value = 0
    lines = state.rows + state.cols + state.diags

    for line in lines:
        for i in range(len(line) - 5 + 1):
            value += get_line_point(state, line[i:i+5])
    
    return value