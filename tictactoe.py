import itertools
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


# Utilities

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

def get_positions_by_item(array, item, criteria=None):
    criteria = criteria or (lambda array,item: array == item)

    return map(lambda x,y: (numpy.array([x]), numpy.array([y])),
        *numpy.where(criteria(array, item)))

def is_unplayed(board, position):
    position = position_to_array(position)
    return board[position][0] == UNPLAYED

def try_rotated(selector_func, board, num_rotations=1):
    if num_rotations == 0:
        # fast-path no rotations
        return selector_func(board)

    num_rotations = (4 + num_rotations) % 4
    match = selector_func(numpy.rot90(board, num_rotations))

    def get_original_match(match):
        rotated_board = NEW_BOARD.copy()
        rotated_board[match] = 1
        original_board = numpy.rot90(rotated_board, 4 - num_rotations)
        return numpy.where(original_board == 1)
    
    if isinstance(match, int):
        # match is a scalar, not a position
        return match 

    if isinstance(match, list):
        # match is a list, transform and return all matches
        return [get_original_match(m) for m in match]
            
    if match:
        return get_original_match(match)
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
    if winner:
        return winner
    if not numpy.any(board==UNPLAYED):
        return 0
    return None


#Strategies

def get_all_wins(player, board):
    def match_row(row_num, row):
        matches = []
        if len(row[row==player]) == 2 and len(row[row==UNPLAYED]) == 1:
            matches.append((numpy.array([row_num]), numpy.where(row==UNPLAYED)[0]))
        return matches

    def match_board(board):
        matches = []
        # search rows for a match
        for i, row in enumerate(board):
            matches.extend(match_row(i, row))

        # no match found in rows, try the diagonal
        diagonal_matches = match_row(-1, board.diagonal())
        matches.extend([(index, index) for _, index in diagonal_matches])
        return matches

    matches = []
    matches.extend(match_board(board))
    matches.extend(try_rotated(match_board, board))
    return matches

def win_by_player(player):
    def _win(board):
        matches = get_all_wins(player, board)
        if matches:
            return matches[0]
        else:
            return None
    return _win

win = win_by_player(BOT)
block = win_by_player(OPPONENT)

def generate_forks():
    def prefork_is_possible(permutation, num_wins):
        is_possible = False
        for sub_permutation in itertools.permutations(permutation, 2):
            sub_board = NEW_BOARD.copy()
            for p in sub_permutation:
                sub_board[position_to_array(p)] = 1
            # if more premature blocks are open than wins required for the fork
            # it's not a fork (remember, a fork needs 2 wins to work)
            if len(get_all_wins(1, sub_board)) <= (num_wins - 2):
                is_possible = True
                break
        return is_possible

    forks = []
    for permutation in itertools.permutations(range(1,10), 3):
        board = NEW_BOARD.copy()
        for p in permutation:
            board[position_to_array(p)] = 1
        wins = get_all_wins(1, board)
        num_wins = len(wins)
        if num_wins > 1 and prefork_is_possible(permutation, num_wins):
            # ok it's a fork, populate all the possible 2-win combinations
            for win_combination in itertools.combinations(wins, 2):
                _board = board.copy()
                for position in get_positions_by_item(_board, 0):
                    if position not in win_combination:
                        _board[position] = -1

                # now compare it to existing forks in all rotations
                is_unique = True
                for i in range(4):
                    rotated = numpy.rot90(_board, i)
                    if any([numpy.all(numpy.equal(rotated, fork)) for fork in forks]):
                        is_unique = False
                        break
                if is_unique:
                    forks.append(_board)
    return forks

forks = generate_forks()

def get_all_forks(player, board):
    def match_board(board):
        board_forks = []
        for i, fork in enumerate(forks):
            unplayed_required = set(board[numpy.where(fork==0)]) == set([UNPLAYED])
            played_array = board[numpy.where(fork==1)]
            played_required = len(numpy.where(played_array==player)[0]) == 2 \
                and len(numpy.where(played_array==UNPLAYED)[0]) == 1
            if unplayed_required and played_required:
                positions = get_positions_by_item(fork, 1)
                board_forks.extend([positions[w[0]] for w in numpy.where(played_array==UNPLAYED)])
        return board_forks

    all_forks = []
    for i in range(4):
        all_forks.extend(try_rotated(match_board, board, num_rotations=i))
    return all_forks

def fork_by_player(player):
    def _fork(board):

        all_forks = get_all_forks(player, board)
        if all_forks:
            return all_forks[0]
        return None
    return _fork

fork = fork_by_player(BOT)

def block_fork(board):
    opponent_forks = get_all_forks(OPPONENT, board)
    if opponent_forks: # uh oh, you're about to get forked!
        unplayed_positions = get_positions_by_item(board, UNPLAYED)
        for position in unplayed_positions:
            # hypothetically play each unplayed position
            # to see if it results in a forced block
            # thus avoiding the impending fork
            temp_board = board.copy()
            temp_board[position] = BOT
            block_position = win_by_player(BOT)(temp_board)
            if block_position and block_position not in opponent_forks:
                return position

        # no way we can force a block, choose the best fork to fork them up!
        for opponent_fork in opponent_forks:
            temp_board = board.copy()
            temp_board[opponent_fork] = BOT
            if not get_all_forks(OPPONENT, temp_board):
                return opponent_fork

        # you're totally screwed, give up man
        return opponent_forks[0]
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
                positions = get_positions_by_item(opposite_corners, True)
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
    if get_positions_by_item(board, BOT):
        return None # opening only applies to the first play
    if not get_positions_by_item(board, OPPONENT):
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
    fork,
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
            return position

    # Well, I'm all out of ideas.
    unplayed_positions = get_positions_by_item(board, UNPLAYED)
    return random.choice(unplayed_positions)

def apply_move(board, position, player):
    if not is_unplayed(board, position):
        raise TicTacNo("Position already played.")
    board[position_to_array(position)] = player
    return board


# Actual gameplay

def bot_turn(move_func):
    def _bot_turn(board, labels):
        print "My move"
        return move_func(board)
    return _bot_turn

def opponent_turn(move_func):
    def _opponent_turn(board, labels):
        print 'You are "%s"' % labels[OPPONENT]
        print render_board(board, labels)
        return move_func(board)
    return _opponent_turn

def play(opponent_move_func=None, first_player=None):
    def default_opponent_move_func(board):
        while 1:
            try:
                try:
                    position = int(raw_input('Your move: '))
                except ValueError:
                    raise TicTacNo("That's not even a number!")
                if not isinstance(position, int) or not (1 <= position <= 9):
                    raise TicTacNo("Invalid position value.")
                return apply_move(board, position, OPPONENT)
            except TicTacNo, e:
                print "Tic Tac NO! (%s)" % e
    opponent_move_func = opponent_move_func or default_opponent_move_func

    turns = {
        BOT: bot_turn(lambda board: apply_move(board, pick_best_move(board), BOT)),
        OPPONENT: opponent_turn(opponent_move_func),
    }

    players = [BOT, OPPONENT]
    if first_player is not None:
        players.sort(key=lambda player: player == first_player and -1 or 1)
    else:
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
            if winner == BOT:
                print "I win! I am invincible!"
            elif winner == OPPONENT:
                print "You win! I am invinc"
                1/0
            else:
                print "I did not lose! I am invincible!"
            break
        current_player = players[(players.index(current_player) + 1) % len(players)]

    print "Final board:"
    print render_board(board, labels)
    return winner

if __name__ == "__main__":
    play()