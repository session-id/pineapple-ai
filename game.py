from collections import namedtuple
import itertools

# rows: list of lists for top, middle, bottom rows
# draw: whatever has been drawn
# remaining: set of remaining cards
PineappleGame1State = namedtuple('PineappleGame1State', ['rows', 'draw', 'remaining'])

CARD_VALUES = '23456789TJQKA'

def card_value(card):
  return CARD_VALUES.index(card[0]) + 2

def compute_hand(cards):
  # Sort cards descending
  cards.sort(lambda x, y: card_value(y) - card_value(x))
  if len(cards) > 3:
    # TODO: Check flushes, straights
    pass
  mults = []
  cur_streak = 1
  for i in range(len(cards) - 1):
    if cards[i][0] == cards[i+1][0]:
      cur_streak += 1
    else:
      mults += [(cur_streak, card_value(cards[i]))]
      cur_streak = 1
  mults += [(cur_streak, card_value(cards[i]))]
  mults.sort(lambda x, y: -cmp(x, y))

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
  return tuple([hand_name] + [x[1] for x in mults])

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