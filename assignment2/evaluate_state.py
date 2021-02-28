from board_util import (
    BLACK,
    WHITE
)

CELLS_PER_LINE = 5
THREE_IN_FIVE = 4
FOUR_IN_FIVE = 12
FIVE_IN_FIVE = 1000000000

def count_to_value(count):
    if count == 3:
        return THREE_IN_FIVE
    elif count == 4:
        return FOUR_IN_FIVE
    elif count == 5:
        return FIVE_IN_FIVE
    else:
        return count


def get_5cell_line_value(state, line):
    count_black = 0
    count_white = 0

    for cell in line:
        cell_color = state.board[cell]

        if cell_color == BLACK:
            count_black += 1
        elif cell_color == WHITE:
            count_white += 1

    if count_black > 0 and count_white > 0:
        return 0

    if state.current_player == BLACK:
        return count_to_value(count_black) - count_to_value(count_white)
    else:
        return count_to_value(count_white) - count_to_value(count_black)

def evaluate_state_forToPlay(state):
    value = 0
    lines = state.rows + state.cols + state.diags

    for line in lines:
        for i in range(len(line) - CELLS_PER_LINE + 1):
            value += get_5cell_line_value(state, line[i:i+CELLS_PER_LINE])
    
    return value