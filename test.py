"""
Test script which walks a decision tree until all possible
game permutations are exhausted.
"""
from collections import defaultdict

import numpy

from tictactoe import UNPLAYED, BOT, OPPONENT, BOARD_SIZE, \
    apply_move, get_positions_by_item, play

def array_to_position(array):
    if isinstance(array, tuple):
        x,y = BOARD_SIZE
        return array[0][0] * x + array[1][0] + 1 # 1-index
    return array

def get_first_available(branch, available_positions):
    position_numbers = [array_to_position(p) for p in available_positions]
    for position_number in position_numbers:
        if position_number not in branch['branches']:
            branch['branches'][position_number] = {
                'exhausted': False,
                'branches': {},
            }
        if not branch['branches'][position_number]['exhausted']:
            return position_number
    return None

current_branch = None
def opponent_move_func(board):
    global current_branch
    available_positions = get_positions_by_item(board, UNPLAYED)
    position = get_first_available(current_branch, available_positions)
    if position is None:
        current_branch['exhausted'] = True
        position = available_positions[0]
    apply_move(board, position, OPPONENT)
    current_branch = current_branch['branches'][array_to_position(position)]
    return board

def play_all_games():
    global current_branch
    for first_player in (OPPONENT, BOT):
        root = {
            'branches': {},
            'exhausted': False,
        }
        while not root['exhausted']:
            current_branch = root
            winner = play(opponent_move_func, first_player=first_player)
            current_branch['exhausted'] = True

if __name__ == "__main__":
    play_all_games()
