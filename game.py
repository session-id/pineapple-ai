from collections import namedtuple
import itertools

# rows: list of lists for top, middle, bottom rows
# draw: whatever has been drawn
# remaining: set of remaining cards
PineappleGame1State = namedtuple('PineappleGame1State', ['rows', 'draw', 'remaining'])

CARD_VALUES = '23456789TJQKA'
HAND_ORDER = reversed(['StFl', '4', '3+2', 'Fl', 'St', '3', '2+2', '2', '1'])
HAND_ORDER_DICT = {}
for i, hand_name in enumerate(HAND_ORDER):
  HAND_ORDER_DICT[hand_name] = i

def card_value(card):
  return CARD_VALUES.index(card[0]) + 2

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
    assert len(hand1) == len(hand2)
    return cmp(hand1[1:], hand2[1:])

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

game = PineappleGame1()

def ranking_test():
  flush = compute_hand(['2H', '3H', '5H', '6H', 'KH'])
  king_high = compute_hand(['2H', '3H', '5H', '6H', 'KS'])
  straight = compute_hand(['2H', '3H', '5H', '6H', '4C'])
  triple = compute_hand(['5D', '5S', '5H', '4H', 'AC'])
  wheel = compute_hand(['2H', '3H', '5H', 'AH', '4C'])
  straight_flush = compute_hand(['2H', '3H', '5H', 'AH', '4H'])
  worse_king_high = compute_hand(['2H', '3H', '4H', '6H', 'KS'])
  two_pair = compute_hand(['2H', '2D', 'AH', '6H', '6C'])
  worse_two_pair = compute_hand(['2H', '2D', 'KD', '6H', '6C'])
  quad = compute_hand(['5C', '5S', '5H', 'AH', '5D'])
  full_house = compute_hand(['5C', '5S', '5H', 'AH', 'AD'])
  pair = compute_hand(['2H', '2D', 'AH', '6H', '7C'])

  def compare_test(hand1, hand2):
    #print hand1, 'vs', hand2, ':', compare_hands(hand1, hand2)
    return compare_hands(hand1, hand2)

  assert compare_test(flush, king_high) == 1
  assert compare_test(king_high, flush) == -1
  assert compare_test(wheel, straight) == -1
  assert compare_test(straight_flush, triple) == 1
  assert compare_test(triple, king_high) == 1
  assert compare_test(wheel, wheel) == 0
  assert compare_test(worse_king_high, king_high) == -1
  assert compare_test(two_pair, worse_two_pair) == 1
  assert compare_test(two_pair, two_pair) == 0
  assert compare_test(straight_flush, quad) == 1
  assert compare_test(quad, full_house) == 1
  assert compare_test(full_house, flush) == 1
  assert compare_test(flush, straight) == 1
  assert compare_test(straight, triple) == 1
  assert compare_test(triple, two_pair) == 1
  assert compare_test(two_pair, pair) == 1
  assert compare_test(pair, king_high) == 1

  print "Ranking test passed!"

ranking_test()