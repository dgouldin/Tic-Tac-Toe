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

def get_positions_matching(array, match_item):
    return map(lambda x,y: (numpy.array([x]), numpy.array([y])),
        *numpy.where(array==match_item))

def is_unplayed(board, position):
    position = position_to_array(position)
    return board[position][0] == UNPLAYED

def try_rotated(selector_func, board, num_rotations=1):
    if num_rotations == 0:
        # fast-path no rotations
        return selector_func(board)

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

def fork(player):
    def _fork(board):
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
                if len(row[row==player]) == 2 and len(row[row==UNPLAYED]) == 1:
                    positions = get_positions_matching(fork, True)
                    return positions[numpy.where(row==UNPLAYED)[0][0]]
            return None

        for i in range(4):
            match = try_rotated(match_board, board, num_rotations=i)
            if match:
                return match
        return None
    return _fork

def block_fork(board):
    opponent_fork = fork(OPPONENT)(board)
    if opponent_fork: # uh oh, you're about to get forked!
        unplayed_positions = get_positions_matching(board, UNPLAYED)
        for position in unplayed_positions:
            # hypothetically play each unplayed position
            # to see if it results in a forced block
            # thus avoiding the impending fork
            temp_board = board.copy()
            temp_board[position] = BOT
            block_position = one_to_win(BOT)(temp_board)
            if block_position and block_position != opponent_fork:
                return position

        # no way we can force a block, fork them up!
        return opponent_fork
    return None

def center(board):
    x,y = BOARD_SIZE
    if board[x/2, y/2] == UNPLAYED:
        return (numpy.array([x/2]), numpy.array([y/2]))
    return None

def opposite_corner(board):
    opposite_corners = numpy.array([
        [False, True,  False],
        [True,  False, False],
        [False, False, False],
    ])

    def match_board(board):
        if board[0,0] == OPPONENT:
            row = board[opposite_corners]
            if len(row[row==UNPLAYED]):
                positions = get_positions_matching(opposite_corners, True)
                return positions[numpy.where(row==UNPLAYED)[0][0]]
        return None

    for i in range(4):
        match = try_rotated(match_board, board, num_rotations=i)
        if match:
            return match
    return None

def empty_corner(board):
    
    def match_board(board):
        if board[0,0] == UNPLAYED:
            return (numpy.array([0]), numpy.array([0]))

    for i in range(4):
        match = try_rotated(match_board, board, num_rotations=i)
        if match:
            return match
    return None

def empty_side(board):

    def match_board(board):
        if board[0,1] == UNPLAYED:
            return (numpy.array([0]), numpy.array([1]))

    for i in range(4):
        match = try_rotated(match_board, board, num_rotations=i)
        if match:
            return match
    return None

def opening(board):
    if get_positions_matching(board, BOT):
        return None # opening only applies to the first play
    if not get_positions_matching(board, OPPONENT):
        return empty_corner(board)
    else:
        corners = numpy.array([
            [True,  False, True ],
            [False, False, False],
            [True,  False, True ],
        ])
        if numpy.any(board[corners] == OPPONENT):
            return center(board)

        x,y = BOARD_SIZE
        if board[x/2, y/2] == OPPONENT:
            return empty_corner(board)
        return center(board)

best_moves = [
    opening,
    win,
    block,
    fork(BOT),
    block_fork,
    center,
    opposite_corner,
    empty_corner,
    empty_side,
]

def pick_best_move(board):
    position = None
    for move in best_moves:
        position = move(board)
        if position is not None:
            print "Used %s" % move
            return position

    # Well, I'm all out of ideas.
    unplayed_positions = get_positions_matching(board, UNPLAYED)
    return random.choice(unplayed_positions)

def apply_move(board, position, player):
    if not is_unplayed(board, position):
        raise TicTacNo("Position already played.")
    board[position_to_array(position)] = player
    return board

def bot_turn(board, labels):
    print "My move"
    return apply_move(board, pick_best_move(board), BOT)

def opponent_turn(board, labels):
    print 'You are "%s"' % labels[OPPONENT]
    print render_board(board, labels)
    while 1:
        try:
            position = input('Your move: ')
            return apply_move(board, position, OPPONENT)
        except TicTacNo, e:
            print "Tic Tac NO! (%s)" % e

turns = {
    BOT: bot_turn,
    OPPONENT: opponent_turn,
}

if __name__ == "__main__":
    players = [BOT, OPPONENT]
    random.shuffle(players)

    if players[0] == BOT:
        print "I go first. You will surely lose."
        labels = {
            BOT: 'x',
            OPPONENT: 'o',
        }
    else:
        print "You go first ... this time. (It does not matter. You will be crushed.)"
        labels = {
            BOT: 'o',
            OPPONENT: 'x',
        }
        

    current_player = players[0]
    board = NEW_BOARD.copy()
    winner = None
    while 1:
        board = turns[current_player](board, labels)
        winner = find_winner(board)
        if winner is not None:
            break
        current_player = players[(players.index(current_player) + 1) % len(players)]

    print "Final board:"
    print render_board(board, labels)
