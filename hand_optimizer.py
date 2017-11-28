from collections import defaultdict
import itertools
import random

import game as g

# Returns all possible hands that can be made at the given row with existing row and future
# draw. Returns hands sorted in decreasing order.
def possible_hands(row, row_num, draw):
  row = g.sort_cards(row, inc=False)
  draw = g.sort_cards(draw, inc=False)
  row_mults = g.cards_to_mults(row)
  draw_mults = g.cards_to_mults(draw)

  flushes = []
  straights = []

  if row_num >= 1:
    suit_counts = defaultdict(int)
    for card in draw:
      suit_counts[card[1]] += 1

    # Check flush possibilities
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
            straights += [('St', i + 4)]

    # TODO: Add straight flush

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

  # Eliminate useless single hands
  all_values = sorted(list(set([g.card_value(card) for card in row] + [g.card_value(card) for card in draw])))
  if len(all_values) < g.ROW_LENGTHS[row_num]:
    min_single = 15
  else:
    min_single = all_values[g.ROW_LENGTHS[row_num] - 1]
  if len(row_mults) > 0:
    min_single = max(min_single, row_mults[0][1])
  singles = [x for x in singles if x[1] >= min_single]

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
            full_houses += [('3+2', value, value2)]
    # Two pair logic
    for _, value in pairs:
      for _, value2 in pairs:
        if value > value2:
          if 4 - row_mults_dict[value] - row_mults_dict[value2] + len(row) <= g.ROW_LENGTHS[row_num]:
            two_pairs += [('2+2', value, value2)]

  # Throw away higher hands that are too low to be made
  if row_num >= 1:
    if len(all_values) == 2:
      pairs = triples = two_pairs = []
    if len(all_values) == 3:
      pairs = []

  # Throw out hands that are under current hand
  if len(row_mults) > 0:
    if row_mults[0][0] >= 2:
      singles = []
      if len(row_mults) >= 2 and row_mults[1][0] >= 2:
        pairs = [] # Overriden by two pair
        triples = [] # Overridden by full house
      else:
        pairs = [x for x in pairs if x[1] == row_mults[0][1]]
    if row_mults[0][0] >= 3:
      two_pairs = []
      pairs = []
    if row_mults[0][0] == 4:
      full_houses = []
      triples = []

  all_hands = flushes + straights + singles + pairs + triples + quads + two_pairs + full_houses
  return sorted(all_hands, lambda x, y: -g.compare_hands(x, y))

# Given the hands in each row in abbreviated format, computes the total royalties
def total_royalties(hands):
  total = 0
  for row_num, hand in enumerate(hands):
    total += g.royalties(hand, row_num)
  return total

# Returns whether or not the specified combo can be made from rows and draw. Possible input hands:
# ('Fl', Suit)
# ('St', End Card)
# ('3+2', Triple, Pair)
# ('2+2', High, Low)
# ('4', High)
# ('3', High)
# ('2', High)
# ('1', High)
# Also needs to perform finer grained checks to ensure final hand doesn't bust.
def is_makeable(rows, draw, combo, precom):
  possible_completions = []
  # fillers_needed will contain the list of fillers required
  fillers_needed = [0] * len(rows)
  # filler_avoid will contain values that must be avoided at the given rows
  # Also, note that filler cannot contain pairs
  filler_avoid = [set() for _ in xrange(len(rows))]

  # TODO: stop caring about suit if no flushes are present

  for row_num, (row, hand) in enumerate(zip(rows, combo)):
    # 5 card hands
    if hand[0] == 'St':
      draw_possibilities = []
      for needed_value in xrange(hand[1] - 4, hand[1] + 1):
        if needed_value == 1:
          needed_value == 14
        if needed_value not in precom['all_row_values'][row_num]:
          # Need to grab from draw
          possible_fills = precom['draw_values'][needed_value]
          assert len(possible_fills) != 0
          draw_possibilities += [possible_fills]
      possible_completions += [list(itertools.product(*draw_possibilities))]
    elif hand[0] == 'Fl':
      suit = hand[1]
      num_left = g.ROW_LENGTHS[row_num] - len(row)
      possible_completions += [list(itertools.combinations(precom['draw_suits'][suit], num_left))]
    elif hand[0] == '3+2':
      _, triple_value, pair_value = hand
      needed = 3 - len(precom['all_row_values'][row_num][triple_value])
      triple_possibilities = list(itertools.combinations(precom['draw_values'][triple_value], needed))
      needed = 2 - len(precom['all_row_values'][row_num][pair_value])
      pair_possibilities = list(itertools.combinations(precom['draw_values'][pair_value], needed))
      possibilities = [x + y for x, y in itertools.product(triple_possibilities, pair_possibilities)]
      possible_completions += [possibilities]

    # Hands requiring fillers
    elif hand[0] == '4':
      _, quad_value = hand
      possible_completions += [[tuple(precom['draw_values'][quad_value])]]
      fillers_needed[row_num] = 1 - (len(row) - len(precom['all_row_values'][row_num][quad_value]))
    elif hand[0] == '2+2':
      _, high_value, low_value = hand
      needed = 2 - len(precom['all_row_values'][row_num][high_value])
      triple_possibilities = list(itertools.combinations(precom['draw_values'][high_value], needed))
      needed = 2 - len(precom['all_row_values'][row_num][low_value])
      pair_possibilities = list(itertools.combinations(precom['draw_values'][low_value], needed))
      possibilities = [x + y for x, y in itertools.product(triple_possibilities, pair_possibilities)]
      possible_completions += [possibilities]
      fillers_needed[row_num] = 1 - (len(row) - len(precom['all_row_values'][row_num][high_value])
                                     - len(precom['all_row_values'][row_num][low_value]))
      filler_avoid[row_num].add(high_value)
      filler_avoid[row_num].add(low_value)
    elif hand[0] == '3':
      _, triple_value = hand
      needed = 3 - len(precom['all_row_values'][row_num][triple_value])
      possible_completions += [list(itertools.combinations(precom['draw_values'][triple_value], needed))]
      if row_num >= 1:
        fillers_needed[row_num] = 2 - (len(row) - len(precom['all_row_values'][row_num][triple_value]))
      for value in precom['all_row_values'][row_num]:
        filler_avoid[row_num].add(value)
    elif hand[0] == '2':
      _, pair_value = hand
      needed = 2 - len(precom['all_row_values'][row_num][pair_value])
      possible_completions += [list(itertools.combinations(precom['draw_values'][pair_value], needed))]
      fillers_needed[row_num] = (3 if row_num >= 1 else 1) - (len(row) - len(precom['all_row_values'][row_num][pair_value]))
      for value in precom['all_row_values'][row_num]:
        filler_avoid[row_num].add(value)
    elif hand[0] == '1':
      _, single_value = hand
      needed = 1 - len(precom['all_row_values'][row_num][single_value])
      possible_completions += [list(itertools.combinations(precom['draw_values'][single_value], needed))]
      fillers_needed[row_num] = (4 if row_num >= 1 else 2) - (len(row) - len(precom['all_row_values'][row_num][single_value]))
      for value, count in precom['all_row_values'][row_num].iteritems():
        if len(count) > 0:
          filler_avoid[row_num].add(value)
      for value in xrange(single_value, g.MAX_VALUE):
        filler_avoid[row_num].add(value)
    else:
      raise RuntimeError("Unrecognized hand type {}".format(hand))

  # print "Possible completions:", possible_completions
  # print "Fillers needed:", fillers_needed
  # print "Filler avoid:", filler_avoid

  # TODO: Also make sure flush is never accidentally made

  # Sort from most constrained to least constrained
  possible_completions.sort(lambda x, y: cmp(len(x), len(y)))
  for completion in itertools.product(*possible_completions):
    possible = True
    # Check to see no cards overlap
    cards_left = set(draw)
    for cards in completion:
      for card in cards:
        if card not in cards_left:
          possible = False
          break
        cards_left.remove(card)
      if not possible:
        break
    if not possible:
      continue
    # Try to assign filler
    possible_fillers = [[] for _ in xrange(g.NUM_ROWS)]
    for card in cards_left:
      for i, avoid_set in enumerate(filler_avoid):
        if card not in avoid_set:
          possible_fillers[i] += [card]
    filler_combos = [list(itertools.combinations(possible_fillers[i], fillers_needed[i]))
                     for i in xrange(g.NUM_ROWS)]
    filler_combos.sort(lambda x, y: cmp(len(x), len(y)))
    for filler_completion in itertools.product(*filler_combos):
      filler_possible = True
      cards_left2 = set(cards_left)
      for cards in filler_completion:
        for card in cards:
          if card not in cards_left2:
            filler_possible = False
            break
          cards_left2.remove(card)
        if not filler_possible:
          break
      if not filler_possible:
        continue
      return True
  
  return False

# Given a set of cards, constructs a dictionary mapping values to cards
def tabulate_values(cards):
  counts = defaultdict(list)
  for card in cards:
    counts[g.card_value(card)] += [card]
  return counts

# Given a set of cards, constructs a dictionary mapping suits to cards
def tabulate_suits(cards):
  counts = defaultdict(list)
  for card in cards:
    counts[card[1]] += [card]
  return counts

# Given the current rows and a future draw, return the highest royalty value achievable from the
# current hand.
# If return_combo is True, it will also return the best combo (None if busted)
def optimize_hand(rows, draw, return_combo=False):
  num_play = sum(g.ROW_LENGTHS) - sum(len(row) for row in rows)
  hands_for_row = []
  for row_num, row in enumerate(rows):
    hands_for_row += [possible_hands(row, row_num, draw)]

  possible_combos = []
  for row1, row2, row3 in itertools.product(*hands_for_row):
    # Skip bust hands
    # WARNING: currently, the use of >= makes it impossible to have two rows with the same
    # hand name (you can't have two different two pairs with the same high card on different rows)
    if g.compare_hands(row1, row2) >= 0 or g.compare_hands(row2, row3) >= 0:
      continue
    possible_combos += [(row1, row2, row3)]

  hands_with_royalties = sorted([(total_royalties(combo), combo) for combo in possible_combos], lambda x, y: -cmp(x,y))
  precom = {
    'all_row_values': [tabulate_values(row) for row in rows],
    'draw_values': tabulate_values(draw),
    'draw_suits': tabulate_suits(draw),
  }
  for royalties, combo in hands_with_royalties:
    if is_makeable(rows, draw, combo, precom):
      if return_combo:
        return royalties, combo
      return royalties

  # No hands were makeable, only bust is possible
  if return_combo:
    return g.BUST_PENALTY, None
  return g.BUST_PENALTY
