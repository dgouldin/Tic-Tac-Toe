import numpy
import random

UNPLAYED, OPPONENT, BOT = 0, 1, 2
BOARD_SIZE = (3, 3)
NEW_BOARD = numpy.zeros(BOARD_SIZE, dtype=int)

BOARD_TEMPLATE = """
 %s | %s | %s 
---|---|---
 %s | %s | %s 
---|---|---
 %s | %s | %s 
"""

class TicTacNo(Exception):
    pass

def render_board(board, labels):
    x,y = BOARD_SIZE
    board_str = numpy.array([''] * x * y).reshape(BOARD_SIZE)
    keys = numpy.array([str(i) for i in range(1, 10)]).reshape(3,3)

    # put labels in place of played positions
    if numpy.any(board == OPPONENT):
        board_str[numpy.where(board == OPPONENT)] = labels[OPPONENT]
    if numpy.any(board == BOT):
        board_str[board == BOT] = labels[BOT]
    # populate the remaining positions with their key equivalents
    board_str = numpy.choose(board == 0, (board_str, keys))
    return BOARD_TEMPLATE % tuple(board_str.flatten().tolist())

def position_to_array(position):
    if isinstance(position, int):
        x,y = BOARD_SIZE
        position -= 1 # positions displayed to the user are 1-based
        return (numpy.array([position / x]), numpy.array([position % x]))
    return position

def is_unplayed(board, position):
    position = position_to_array(position)
    return board[position][0] == UNPLAYED

def try_rotated(selector_func, board, num_rotations=1):
    num_rotations = (4 + num_rotations) % 4
    match = selector_func(numpy.rot90(board, num_rotations))

    if isinstance(match, int):
        return match # match is a scalar, not a position

    if match:
        rotated_board = NEW_BOARD.copy()
        rotated_board[match] = 1
        original_board = numpy.rot90(rotated_board, 4 - num_rotations)
        return numpy.where(original_board == 1)
    return None

def find_winner(board):
    def match_row(row):
        uniques = list(set(row)) # uniquify!
        if len(uniques) == 1 and uniques[0] != UNPLAYED:
            return uniques[0]
        return None

    def match_board(board):
        for row in board:
            match = match_row(row)
            if match:
                return match

        match = match_row(board.diagonal())
        if match:
            return match
        return None

    winner = match_board(board) or try_rotated(match_board, board)

    if winner is not None:
        if winner == BOT:
            print "I win! I am invincible!"
        else:
            print "You win! I am invinc"
            1/0
    if not numpy.any(board==UNPLAYED):
        print "I did not lose! I am invincible!"
        winner = 0
    return winner

def one_to_win(player):
    def _one_to_win(board):
        def match_row(row_num, row):
            if len(row[row==player]) == 2 and len(row[row==UNPLAYED]) == 1:
                return (numpy.array([row_num]), numpy.where(row==UNPLAYED)[0])
            return None

        def match_board(board):
            # search rows for a match
            for i, row in enumerate(board):
                match = match_row(i, row)
                if match:
                    return match

            # no match found in rows, try the diagonal
            match = match_row(-1, board.diagonal())
            if match:
                _, index = match
                return (index, index)
            return None

        return match_board(board) or try_rotated(match_board, board)
    return _one_to_win

win = one_to_win(BOT)
block = one_to_win(OPPONENT)

def fork(board):
    forks = [
        numpy.array([
            [True,  False, False],
            [False, False, False],
            [True,  False, True ],
        ]),
        numpy.array([
            [False, False, False],
            [True,  False, False],
            [True,  False, True ],
        ]),
    ]

    def match_board(board):
        for fork in forks:
            row = board[fork]
            if len(row[row==BOT]) == 2 and len(row[row==UNPLAYED]) == 1:
                positions = map(lambda x,y: (numpy.array([x]), numpy.array([y])),
                    *numpy.where(fork==True))
                return positions[numpy.where(row==UNPLAYED)[0][0]]
        return None

    for i in range(1, 4):
        match = try_rotated(match_board, board, num_rotations=i)
        if match:
            return match
    return None

best_moves = [
    win,
    block,
    fork
]

def pick_best_move(board):
    position = None
    for move in best_moves:
        position = move(board)
        if position is not None:
            return position

    # Well, I'm all out of ideas.
    unplayed_positions = map(lambda x,y: (numpy.array([x]), numpy.array([y])),
        *numpy.where(board==UNPLAYED))
    return random.choice(unplayed_positions)

def apply_move(board, position, player):
    if not is_unplayed(board, position):
        raise TicTacNo("Position already played.")
    board[position_to_array(position)] = player
    return board

if __name__ == "__main__":
    labels = {
        BOT: 'x',
        OPPONENT: 'o',
    }
    board = NEW_BOARD.copy()
    winner = None

    while 1:
        print render_board(board, labels)
        position = None
        while position is None:
            try:
                position = input('Your move: ')
                board = apply_move(board, position, OPPONENT)
            except TicTacNo, e:
                position = None
                print "Tic Tac NO! (%s)" % e
        winner = find_winner(board)
        if winner is not None:
            break

        print "My move"
        board = apply_move(board, pick_best_move(board), BOT)
        winner = find_winner(board)
        if winner is not None:
            break

    print "Final board:"
    print render_board(board, labels)
