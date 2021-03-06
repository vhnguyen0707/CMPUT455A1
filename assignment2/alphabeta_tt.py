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

    good_move = None

    for move in state.sort_moves():
        state.play_move(move, state.current_player)
        value = -alphabeta(state, -beta, -alpha, tt)[0]
        state.undoMove(move)

        if value > alpha:
            alpha = value
            good_move = move
            if alpha == 1:
                break
        
        if value >= beta: 
            result = beta, move
            return storeResult(tt, state, result) 

    result = alpha, good_move
    return storeResult(tt, state, result)

def call_alphabeta_tt(rootState, tt):
    return alphabeta(rootState, -1, 1, tt)
