from collections import defaultdict

import game as g

def possible_hands(row, row_num, draw):
  row = g.sort_cards(row, inc=False)
  draw = g.sort_cards(draw, inc=False)
  row_mults = g.cards_to_mults(row)
  draw_mults = g.cards_to_mults(draw)

  # if row_num == 0:
  #   if len(row) == 0:
  #     draw_mults[0]

  suit_counts = defaultdict(int)
  for card in draw:
    suit_counts[card[1]] += 1

  # Check flush possibilities
  flushes = []
  if len(row) >= 1:
    suit = row[0][1]
    # Check monochrome
    if all(card[1] == suit for card in row):
      if suit_counts[suit] + len(row) >= 5:
        flushes += [('Fl', suit)]
  else:
    for suit in g.SUITS:
      if suit_counts[suit] >= 5:
        flushes += [('Fl', suit)]

  # Check straight possibilities
  straights = []
  all_presences = set()
  for card in row + draw:
    all_presences.add(g.card_value(card))
    # Add ace at 0 for wheel
    if g.card_value(card) == 14:
      all_presences.add(0)
  if len(row) >= 1:
    row_values = [g.card_value(card) for card in row]
    # Range must allow straight
    if max(row_values) - min(row_values) <= 4:
      min_start = max(max(row_values) - 4, 0)
      max_start = min(min(row_values), 10)
      for i in xrange(min_start, max_start + 1):
        possible = True
        for j in xrange(i, i + 5):
          if j not in all_presences:
            possible = False
            break
        if possible:
          straights += ['St', i + 4]

  # Check N of a kind possibilities
  num_left = (3 if row_num == 0 else 5) - len(row)
  row_mults_dict = defaultdict(int, {y: x for x, y in row_mults})
  draw_mults_dict = defaultdict(int, {y: x for x, y in draw_mults})
  singles = []
  pairs = []
  triples = []
  quads = []
  for value in xrange(g.MIN_VALUE, g.MAX_VALUE + 1):
    max_mult = row_mults_dict[value] + min(draw_mults_dict[value], num_left)
    if row_mults_dict[value] <= 1 and max_mult >= 1:
      singles += [('1', value)]
    if row_mults_dict[value] <= 2 and max_mult >= 2:
      pairs += [('2', value)]
    if row_mults_dict[value] <= 3 and max_mult >= 3:
      triples += [('3', value)]
    if row_mults_dict[value] <= 4 and max_mult >= 4:
      quads += [('4', value)]

  # Determine full house / two pair
  two_pairs = []
  full_houses = []
  present_cards = [x[1] for x in row_mults]
  if row_num >= 1:
    # Full house logic
    for _, value in triples:
      for _, value2 in pairs:
        if value2 != value:
          if 5 - row_mults_dict[value] - row_mults_dict[value2] + len(row) <= g.ROW_LENGTHS[row_num]:
            full_houses += [('3+2', value)]
            break
    # Two pair logic
    for _, value in pairs:
      for _, value2 in pairs:
        if value > value2:
          if 4 - row_mults_dict[value] - row_mults_dict[value2] + len(row) <= g.ROW_LENGTHS[row_num]:
            two_pairs += [('2+2', value)]
            break

  # Throw out hands that are under current hand
  if len(row_mults) > 0:
    if row_mults[0][0] >= 2:
      singles = []
      pairs = [x for x in pairs if x[1] >= row_mults[0][1]]
    if row_mults[0][0] >= 3:
      two_pairs = []
      pairs = []
    if row_mults[0][0] == 4:
      full_houses = []
      triples = []

  return flushes + straights + singles + pairs + triples + quads + two_pairs + full_houses

def optimize_hand(rows, draw):
  num_play = sum(g.ROW_LEGNTHS) - sum(len(row) for row in rows)

print possible_hands(['TH', '9H'], 1, ['2H', '2S', 'JC', 'QC', '8C', '7H', 'AH'])
print possible_hands(['TH', '5S'], 1, ['2H', '2S', 'JC', '8C', '7H', '9D', '5C', '5D'])
print possible_hands([], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])
print possible_hands(['TD', 'TS'], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])