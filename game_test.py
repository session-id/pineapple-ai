from game import *

'''
RANKINGS AND ROYALTIES
'''

royal_flush = compute_hand(['AD', 'KD', 'QD', 'TD', 'JD'])
flush = compute_hand(['2H', '3H', '5H', '6H', 'KH'])
king_high = compute_hand(['2H', '3H', '5H', '6H', 'KS'])
straight = compute_hand(['2H', '3H', '5H', '6H', '4C'])
triple_5 = compute_hand(['5D', '5S', '5H', '4H', 'AC'])
wheel = compute_hand(['2H', '3H', '5H', 'AH', '4C'])
straight_flush = compute_hand(['2H', '3H', '5H', 'AH', '4H'])
worse_king_high = compute_hand(['2H', '3H', '4H', '6H', 'KS'])
two_pair = compute_hand(['2H', '2D', 'AH', '6H', '6C'])
worse_two_pair = compute_hand(['2H', '2D', 'KD', '6H', '6C'])
quad = compute_hand(['5C', '5S', '5H', 'AH', '5D'])
full_house = compute_hand(['5C', '5S', '5H', 'AH', 'AD'])
pair_2 = compute_hand(['2H', '2D', 'AH', '6H', '7C'])
pair_A = compute_hand(['2H', 'AD', 'AH', '6H', '7C'])
pair_2_top = compute_hand(['2H', '2D', 'AH'])
pair_A_top = compute_hand(['2H', 'AD', 'AH'])
triple_5_top = compute_hand(['5H', '5D', '5C'])

def ranking_test():
  def compare_test(hand1, hand2):
    return compare_hands(hand1, hand2)

  assert compare_test(royal_flush, straight_flush) == 1
  assert compare_test(royal_flush, royal_flush) == 0
  assert compare_test(flush, king_high) == 1
  assert compare_test(king_high, flush) == -1
  assert compare_test(wheel, straight) == -1
  assert compare_test(straight_flush, triple_5) == 1
  assert compare_test(triple_5, king_high) == 1
  assert compare_test(wheel, wheel) == 0
  assert compare_test(worse_king_high, king_high) == -1
  assert compare_test(two_pair, worse_two_pair) == 1
  assert compare_test(two_pair, two_pair) == 0
  assert compare_test(straight_flush, quad) == 1
  assert compare_test(quad, full_house) == 1
  assert compare_test(full_house, flush) == 1
  assert compare_test(flush, straight) == 1
  assert compare_test(straight, triple_5) == 1
  assert compare_test(triple_5, two_pair) == 1
  assert compare_test(two_pair, pair_2) == 1
  assert compare_test(pair_2, pair_A) == -1
  assert compare_test(pair_2_top, pair_A_top) == -1
  assert compare_test(pair_2, king_high) == 1

  # Top vs Mid comparisons
  assert compare_test(triple_5, triple_5_top) == 0
  assert compare_test(pair_A, triple_5_top) == -1

  print "Ranking test passed!"

def royalties_test():
  assert royalties(pair_2_top, 0, fl_bonus=False) == 0
  assert royalties(pair_A_top, 0, fl_bonus=False) == 9
  assert royalties(triple_5_top, 0, fl_bonus=False) == 13
  assert royalties(pair_2, 1, fl_bonus=False) == 0
  assert royalties(triple_5, 1, fl_bonus=False) == 2
  assert royalties(wheel, 1, fl_bonus=False) == 4
  assert royalties(flush, 1, fl_bonus=False) == 8
  assert royalties(full_house, 1, fl_bonus=False) == 12
  assert royalties(quad, 1, fl_bonus=False) == 20
  assert royalties(straight_flush, 1, fl_bonus=False) == 30
  assert royalties(royal_flush, 1, fl_bonus=False) == 50
  assert royalties(two_pair, 2, fl_bonus=False) == 0
  assert royalties(triple_5, 2, fl_bonus=False) == 0
  assert royalties(wheel, 2, fl_bonus=False) == 2
  assert royalties(flush, 2, fl_bonus=False) == 4
  assert royalties(full_house, 2, fl_bonus=False) == 6
  assert royalties(quad, 2, fl_bonus=False) == 10
  assert royalties(straight_flush, 2, fl_bonus=False) == 15
  assert royalties(royal_flush, 2, fl_bonus=False) == 25

  # Total royalties
  assert total_royalties([
      ['AD', 'AD', 'KD'],
      ['3S', '3H', '4D', '4H', '5C'],
      ['6S', '6S', '7S', '7C', '7D']
    ], fl_bonus=False) == 15
  assert total_royalties([
      ['AD', 'AD', 'KD'],
      ['3S', '3H', '4D', '4H', '5C'],
      ['6S', '6S', '7S', '7C', '8D']
    ], fl_bonus=False) == 9

  # Bust
  assert total_royalties([
      ['AD', 'AD', 'AC'],
      ['3S', '3H', '4D', '4H', '5C'],
      ['6S', '6S', '7S', '7C', '7D']
    ], fl_bonus=False) is None
  assert total_royalties([
      ['AD', 'AD', 'AC'],
      ['3S', '3H', '8D', '8H', '8C'],
      ['6S', '6S', '7S', '7C', '7D']
    ], fl_bonus=False) is None
  assert is_bust([triple_5_top, pair_2, full_house])
  assert is_bust([triple_5_top, quad, full_house])

  print "Royalties test passed!"

ranking_test()
royalties_test()

'''
PARTIAL HAND TESTING LOGIC
'''

p_triple_5 = compute_hand(['5D', '5S', '5H', '4H'])
p_king_high = compute_hand(['2H', '6H', 'KS'])
p_worse_king_high = compute_hand(['2H', '3H', '4H' 'KS'])
p_two_pair = compute_hand(['2H', '2D','6H', '6C'])
p_pair_2 = compute_hand(['2H', '2D', 'AH'])
p_pair_A = compute_hand(['AD', 'AH', '6H'])
p_worse_pair_A = compute_hand(['AD', 'AH'])
p_ten_high = compute_hand(['TD'])
p_seven_high = compute_hand(['2D', '6H', '7H'])

def partial_ranking_test():
  assert compare_hands(p_triple_5, p_two_pair) == 1
  assert compare_hands(p_worse_pair_A, p_pair_A) == -1
  assert compare_hands(p_pair_2, p_pair_2) == 0
  assert compare_hands(p_pair_A, p_pair_2) == 1
  assert compare_hands(p_king_high, p_worse_king_high) == 1
  assert compare_hands(p_two_pair, p_pair_A) == 1
  assert compare_hands(p_ten_high, p_seven_high) == 1

  print "Partial ranking test passed!"

partial_ranking_test()

'''
GAME LOGIC
'''

game = PineappleGame1()

def start_state_test():
  # Remove card from copy of initial state
  start_state = game.get_start_state(hero_first=True)
  assert len(start_state.remaining) == 47
  assert len(start_state.draw) == 5
  removal_cards = ['2C', '3C', '4C', '5C']
  for remove_card in removal_cards:
    if remove_card not in start_state.draw:
      start_state.remaining.remove(remove_card)
      break
  assert remove_card in game.cards

  start_state = game.get_start_state(hero_first=False)
  assert len(start_state.remaining) == 42
  assert len(start_state.draw) == 5

  print 'Start state test passed!'

def actions_test():
  start_state = game.get_start_state(hero_first=True)
  # Make fake state with incongruous remaining
  state = PineappleGame1State(
      rows = [['AH'], ['AD', 'AS', '2D', '2S'], ['4H', '5H']],
      draw = ['6H', '7H', 'AC'],
      remaining = start_state.remaining
    )
  a = tuple(sorted([
      (('6H', 0), ('7H', 0)),
      (('6H', 0), ('7H', 1)),
      (('6H', 0), ('7H', 2)),
      (('6H', 1), ('7H', 0)),
      (('6H', 1), ('7H', 2)),
      (('6H', 2), ('7H', 0)),
      (('6H', 2), ('7H', 1)),
      (('6H', 2), ('7H', 2)),
      (('6H', 0), ('AC', 0)),
      (('6H', 0), ('AC', 1)),
      (('6H', 0), ('AC', 2)),
      (('6H', 1), ('AC', 0)),
      (('6H', 1), ('AC', 2)),
      (('6H', 2), ('AC', 0)),
      (('6H', 2), ('AC', 1)),
      (('6H', 2), ('AC', 2)),
      (('7H', 0), ('AC', 0)),
      (('7H', 0), ('AC', 1)),
      (('7H', 0), ('AC', 2)),
      (('7H', 1), ('AC', 0)),
      (('7H', 1), ('AC', 2)),
      (('7H', 2), ('AC', 0)),
      (('7H', 2), ('AC', 1)),
      (('7H', 2), ('AC', 2)),
    ]))
  if tuple(sorted(game.actions(state))) != a:
    print sorted(game.actions(state))
    print a
    raise RuntimeError("Difference found!")

  # Some combinatorics
  num_opening = 2 * 2 * 10 + 10 * 2 ** 3 + 5 * 2 ** 4 + 2 ** 5
  assert len(game.actions(start_state)) == num_opening

  print 'Actions test passed!'

def game_royalties_test():
  # Make fake state with incongruous remaining
  state = PineappleGame1State(
      rows = [
          ['AH', 'AC', '3D'],
          ['AD', 'AS', '2D', '2S', '7S'],
          ['4H', '5H', '6H', '7H', '8H']
        ],
      draw = None,
      remaining = set()
    )
  assert game.utility(state) == 9 + 15 + FANTASYLAND_BONUS
  state = PineappleGame1State(
      rows = [
          ['3H', '3C', '3D'],
          ['AD', 'AS', '2D', '2S', '7S'],
          ['4H', '5H', '6H', '7H', '8H']
        ],
      draw = None,
      remaining = set()
    )
  assert game.utility(state) == BUST_PENALTY

  print "Game royalties test passed!"


start_state_test()
actions_test()
game_royalties_test()

'''
PineappleGame2 tests
'''

game = PineappleGame2('player')

def adv_game_utilities_test():
  state = PineappleGame2State(
      rows = [
        ['5D', '8S', '4D'],
        ['3S', '5C', '2C', '4C', 'TC'],
        ['7H', 'AH', 'KH', '2H', 'TH']
      ],
      draw = None,
      remaining = set(),
      fake_remaining = set(),
    )
  state.opp_rows = [
    ['QC', 'QD', '8D'],
    ['2D', 'AD', 'KS', '9C', 'JS'],
    ['7C', '6C', '6S', '9S', '7D']
  ]

  assert game.utility(state) == 10
  temp = state.opp_rows
  state.opp_rows = state.rows
  state.rows = temp
  assert game.utility(state) == -10

  state = PineappleGame2State(
      rows = [
        ['AC', 'QD', 'QH'],
        ['AD', 'AS', '6C', '4S', 'KC'],
        ['3D', '3H', '7C', '9C', 'KD']
      ],
      draw = None,
      remaining = set(),
      fake_remaining = set(),
    )
  state.opp_rows = [
    ['4H', 'TC', '5H'],
    ['9D', 'TD', 'JH', 'QC', '9S'],
    ['8D', '8H', '6H', '8C', '6S']
  ]
  assert game.utility(state) == 12

  print "Adversarial game utilities test passed!"

adv_game_utilities_test()