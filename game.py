from collections import namedtuple, defaultdict
import itertools

# rows: list of lists for top, middle, bottom rows
# draw: whatever has been drawn
# remaining: set of remaining cards
PineappleGame1State = namedtuple('PineappleGame1State', ['rows', 'draw', 'remaining'])

'''
CONSTANTS
'''
CARD_VALUES = '23456789TJQKA'
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

'''
GLOBAL FUNCTIONS
'''

# Return the value of the card (from 2 to 14)
def card_value(card):
  return CARD_VALUES.index(card[0]) + 2

# Compute the hand associated with the given cards
# Hands are tuples with the form (hand_name, values...)
def compute_hand(cards):
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
  assert len(hands) == 3
  return compare_hands(hands[0], hands[1]) > 0 or compare_hands(hands[1], hands[2]) > 0

# Compute the total royalties earned from the provided triplet of rows
# Returns None on bust
def total_royalties(triplet):
  assert len(triplet) == 3
  assert len(triplet[0]) == 3
  assert len(triplet[1]) == 5
  assert len(triplet[2]) == 5
  hands = [compute_hand(cards) for cards in triplet]
  if is_bust(hands):
    return None
  return sum(royalties(hand, row) for row, hand in enumerate(hands))

'''
GAME OBJECT
'''

class PineappleGame1(object):
  '''
  A game of Pineapple with only one player and no opponent cards shown.
  '''
  def __init__(self):
    self.cards = [a + b for a, b in itertools.product(CARD_VALUES, 'CDHS')]
    assert len(self.cards) == 52
    self.init_remaining = set(self.cards)

  def is_end(self, state):
    return len(self.rows[0]) == 3 and len(self.rows[1]) == 5 and len(self.rows[2]) == 5

  # Only call when is_end is true
  def utility(self, state):
    # TODO: compute royalties
    raise NotImplementedError

  def actions(self, state):
    open_spaces = [len(x) for x in rows]
    raise NotImplementedError