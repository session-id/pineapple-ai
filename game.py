from collections import namedtuple, defaultdict
import copy
import itertools
import random

# rows: list of lists for top, middle, bottom rows
# draw: whatever has been drawn
# remaining: set of remaining cards
class PineappleGame1State:
  def __init__(self, rows, draw, remaining):
    self.rows = rows
    self.draw = draw
    self.remaining = remaining

'''
GAME CONSTANTS
'''
CARD_VALUES = 'VWXYZ23456789TJQKA'
DECK_CARD_VALUES = '23456789TJQKA'
HAND_ORDER = reversed(['RoFl', 'StFl', '4', '3+2', 'Fl', 'St', '3', '2+2', '2', '1'])
HAND_ORDER_DICT = {}
for i, hand_name in enumerate(HAND_ORDER):
  HAND_ORDER_DICT[hand_name] = i
MID_ROW_ROYALTIES = {
    '3': 2,
    'St': 4,
    'Fl': 8,
    '3+2': 12,
    '4': 20,
    'StFl': 30,
    'RoFl': 50
  }
MID_ROW_ROYALTIES = defaultdict(int, MID_ROW_ROYALTIES)
BOT_ROW_ROYALTIES = {
    'St': 2,
    'Fl': 4,
    '3+2': 6,
    '4': 10,
    'StFl': 15,
    'RoFl': 25
  }
BOT_ROW_ROYALTIES = defaultdict(int, BOT_ROW_ROYALTIES)
ROW_LENGTHS = [3, 5, 5]
NUM_ROWS = 3
FILL_CARDS = ['VF', 'WE', 'XE', 'YE', 'ZE']

'''
PARAMETERS
'''

# Simulates actuality of getting swept, with opponent having 20% bust chance
BUST_PENALTY = -6 * 0.8

'''
GLOBAL FUNCTIONS
'''

# Return the value of the card (from 2 to 14)
def card_value(card):
  return CARD_VALUES.index(card[0]) - 3

# Compute the hand associated with the given cards
# Hands are tuples with the form (hand_name, values...)
def compute_hand(cards):
  # Pad cards with filler cards if incomplete
  if len(cards) <= 3:
    deficit = 3 - len(cards)
  else:
    deficit = 5 - len(cards)
  cards += FILL_CARDS[:deficit]

  # Sort cards descending
  cards.sort(lambda x, y: card_value(y) - card_value(x))
  mults = []
  cur_streak = 1
  for i in range(len(cards) - 1):
    if cards[i][0] == cards[i+1][0]:
      cur_streak += 1
    else:
      mults += [(cur_streak, card_value(cards[i]))]
      cur_streak = 1
  mults += [(cur_streak, card_value(cards[-1]))]
  mults.sort(lambda x, y: -cmp(x, y))

  def to_hand_tuple(hand_name, mults):
    return tuple([hand_name] + [x[1] for x in mults])

  if len(cards) > 3:
    is_straight = is_flush = False
    # Flush
    if all([card[1] == cards[0][1] for card in cards]):
      is_flush = True
    # Straight
    if len(mults) == 5:
      is_straight = True
      straight_mults = sorted(mults)
      for i in range(len(straight_mults) - 1):
        if straight_mults[i+1][1] != straight_mults[i][1] + 1:
          is_straight = False
          break
      if is_straight:
        straight_high = straight_mults[-1][1]
      # Wheel
      elif i == 3 and straight_mults[0][1] == 2 and straight_mults[-1][1] == 14:
        is_straight = True
        straight_high = 5
    if is_straight and is_flush:
      if straight_mults[0][1] == 10:
        return ("RoFl",)
      return ("StFl", straight_high)
    elif is_straight:
      return ("St", straight_high)
    elif is_flush:
      return to_hand_tuple("Fl", mults)

  # Check [NUM] of a kind hands
  if mults[0][0] == 4:
    hand_name = "4"
  elif mults[0][0] == 3:
    if len(mults) > 1 and mults[1][0] == 2:
      hand_name = "3+2"
    else:
      hand_name = "3"
  elif mults[0][0] == 2:
    if mults[1][0] == 2:
      hand_name = "2+2"
    else:
      hand_name = "2"
  else:
    hand_name = "1"
  return to_hand_tuple(hand_name, mults)

# Returns 1 if hand1 > hand2
# Returns -1 if hand1 < hand2
# Returns 0 on tie
def compare_hands(hand1, hand2):
  if HAND_ORDER_DICT[hand1[0]] > HAND_ORDER_DICT[hand2[0]]:
    return 1
  elif HAND_ORDER_DICT[hand1[0]] < HAND_ORDER_DICT[hand2[0]]:
    return -1
  else:
    min_len = min(len(hand1), len(hand2))
    return cmp(hand1[1:min_len], hand2[1:min_len])

# Compute the royalties associated with having the given hand on the given row
def royalties(hand, row):
  if row == 0:
    if hand[0] == '2':
      if hand[1] >= 6:
        return hand[1] - 5
    elif hand[0] == '3':
      return hand[1] + 8
  elif row == 1:
    return MID_ROW_ROYALTIES[hand[0]]
  elif row == 2:
    return BOT_ROW_ROYALTIES[hand[0]]
  else:
    raise RuntimeError("Invalid row: {}".format(row))
  return 0

# Returns whether or not the hands constitute a bust
def is_bust(hands):
  assert len(hands) == NUM_ROWS
  return compare_hands(hands[0], hands[1]) > 0 or compare_hands(hands[1], hands[2]) > 0

# Compute the total royalties earned from the provided rows
# Returns None on bust
def total_royalties(rows):
  assert len(rows) == NUM_ROWS
  for i in xrange(NUM_ROWS):
    assert len(rows[i]) == ROW_LENGTHS[i]
  hands = [compute_hand(cards) for cards in rows]
  if is_bust(hands):
    return None
  return sum(royalties(hand, row) for row, hand in enumerate(hands))

'''
GAME OBJECT
'''

class PineappleGame1(object):
  '''
  A game of Pineapple with only one player and opponent cards shown.
  '''
  def __init__(self):
    cards = [a + b for a, b in itertools.product(DECK_CARD_VALUES, 'CDHS')]
    self.deck_size = 52
    self.cards = set(cards)
    assert len(self.cards) == self.deck_size

  # Randomly choose an initial 5 card draw and create start state
  def get_start_state(self, hero_first):
    cards = copy.deepcopy(self.cards)
    if not hero_first:
      opponent_draw = random.sample(cards, 5)
      for card in opponent_draw:
        cards.remove(card)
    draw = random.sample(cards, 5)
    for card in draw:
      cards.remove(card)
    return PineappleGame1State(rows=[[], [], []], draw=draw, remaining=cards)

  def num_cards_played(self, state):
    return sum(len(x) for x in state.rows)

  def get_remaining_capacities(self, state):
    return [max_cards - len(row) for max_cards, row in zip(ROW_LENGTHS, state.rows)]

  # Returns a list of possible actions from the provided state. States are in the format:
  # ((card1, placement1), (card2, placement2))
  def actions(self, state):
    remaining_capacities = self.get_remaining_capacities(state)
    actions = []

    def find_assigns(i, num_cards, remaining_capacities, cur_assign):
      if i == num_cards:
        return [cur_assign]
      all_assigns = []
      for j in range(NUM_ROWS):
        if remaining_capacities[j] > 0:
          remaining_capacities[j] -= 1
          all_assigns += find_assigns(i+1, num_cards, remaining_capacities, cur_assign + [j])
          remaining_capacities[j] += 1
      return all_assigns

    num_to_play = 5 if len(state.draw) == 5 else 2
    placement_combos = find_assigns(0, num_to_play, remaining_capacities, [])   
    for cards in itertools.combinations(state.draw, num_to_play):
      for placements in placement_combos:
        actions += [tuple(sorted([(card, placement) for card, placement in zip(cards, placements)]))]
    return actions

  # Returns whether the given state is terminal by checking for full rows
  def is_end(self, state):
    return all(len(state.rows[i]) == ROW_LENGTHS[i] for i in range(NUM_ROWS))

  # Given the state and action, takes the action and then randomly simulates the drawing
  # of cards, returning a state.
  # Does not modify the provided state.
  # The input action does not need to be sorted.
  def get_random_outcome(self, state, action):
    state = copy.deepcopy(state)
    action = sorted(action)
    if action not in self.actions(state):
      raise RuntimeError("Illegal Action: {}".format(action))
    for card, placement in action:
      state.rows[placement] += [card]
    if len(action) == 5 and self.deck_size - len(state.remaining) == 5:
      opponent_draw = random.sample(state.remaining, 5)
    else:
      opponent_draw = random.sample(state.remaining, 2)
    for card in opponent_draw:
      state.remaining.remove(card)
    state.draw = random.sample(state.remaining, 3)
    for card in state.draw:
      state.remaining.remove(card)
    return state

  # Only call when is_end is true
  def utility(self, state):
    assert self.is_end(state)
    royalties = total_royalties(state.rows)
    if royalties is None:
      return BUST_PENALTY
    return royalties

  # Pretty print the state for display
  def print_state(self, state):
    discarded = []
    for card in self.cards:
      if card not in state.remaining and\
          not any([card in row or card in state.draw for row in state.rows]):
        discarded += [card]
    print 'Discard:', ' '.join(sorted(discarded, lambda x, y: cmp(card_value(x), card_value(y))))
    for row in state.rows:
      print '| ' + ' '.join(row)
    print 'Draw:', ' '.join(sorted(state.draw))