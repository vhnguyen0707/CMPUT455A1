# cite: course material: alphabeta.py and boolean_negamax_tt.py

from board_util import GoBoardUtil

def storeResult(tt, state, result):
    tt.store(state.hashcode(), result)
    return result

def alphabeta(state, alpha, beta, tt):
    result = tt.lookup(state.hashcode())

    if result is not None:
        return result

    if state.endOfGame():
        result = state.staticallyEvaluateForToPlay(), None
        return storeResult(tt, state, result)

    best_move = None

    for move in state.sort_moves():
        state.play_move(move, state.current_player)
        value = -alphabeta(state, -beta, -alpha, tt)[0]
        state.undoMove(move)

        if value > alpha:
            alpha = value
            best_move = move
            if alpha == 1:
                break
        
        if value >= beta: 
            result = beta, move
            return storeResult(tt, state, result) 

    result = alpha, best_move
    return storeResult(tt, state, result)

# initial call with full window
def call_alphabeta_tt(rootState, tt):
    return alphabeta(rootState, -1, 1, tt)
