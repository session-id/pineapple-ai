import random

import game as g

class BasePolicy(object):
  '''
  Base class for all policies.
  '''

  def __init__(self, game, args=None):
    self.game = game

  # Must return the optimal action as determined by the policy for the given state
  def get_action(self, state):
    raise NotImplementedError


class HumanPolicy(BasePolicy):
  '''
  A policy that asks for human input for every move.
  '''

  def get_action(self, state):
    while True:
      self.game.print_state(state)
      try:
        # Action input format is Pos1 Pos2 ... PosN
        # Example: 0 0 1 2 0
        inp = raw_input("Card placements (space separated, x for discard): ").upper()
        inp = inp.split(' ')
        draw = sorted(state.draw)
        action = tuple(sorted((draw[i], int(inp[i])) for i in range(len(inp)) if inp[i] != 'X'))
        new_state = self.game.get_random_outcome(state, action) # Check if valid
        return action
      except Exception as e:
        print 'Invalid action: {}'.format(e)


class RandomPolicy(BasePolicy):
  '''
  Policy that chooses an action uniformly randomly from all possible actions.
  '''

  def get_action(self, state):
    actions = self.game.actions(state)
    return random.sample(actions, 1)[0]


class BaselinePolicy(BasePolicy):
  '''
  Baseline policy as described in project proposal.

  Starts off by placing cards at or below top_cutoff on top row, those
  at or below mid_cutoff in mid row, and the rest in the bottom row.

  Then, for every 3 card draw, takes the 2 largest cards and slots them according
  to the same rule when possible, otherwise slotting them as low as possible.
  '''

  def __init__(self, game, args):
    super(BaselinePolicy, self).__init__(game, args)
    self.top_cutoff = 4
    self.mid_cutoff = 9

  def value_to_slot(self, value):
    if value <= self.top_cutoff:
      return 0
    elif value <= self.mid_cutoff:
      return 1
    else:
      return 2

  def get_action(self, state):
    remaining_capacities = self.game.get_remaining_capacities(state)
    # Sort in decreasing order
    draw = sorted(state.draw, lambda x, y: g.card_value(y) - g.card_value(x))
    assert len(draw) == 5 or len(draw) == 3
    # Always take highest 2 cards
    if len(draw) == 3:
      draw = draw[:-1]
    values = [g.card_value(card) for card in draw]

    action = []
    for i in range(len(values)):
      desired_row = self.value_to_slot(values[i])
      slotted = False
      # Search downwards first for spots
      for j in range(desired_row, 3):
        if remaining_capacities[j] > 0:
          action += [(draw[i], j)]
          remaining_capacities[j] -= 1
          slotted = True
          break
      if not slotted:
        # Then search upwards
        for j in range(desired_row-1, -1, -1):
          if remaining_capacities[j] > 0:
            action += [(draw[i], j)]
            remaining_capacities[j] -= 1
            slotted = True
            break
      if not slotted:
        self.game.print_state(state)
        raise RuntimeError("Couldn't slot card anywhere!")
    return tuple(action)


class NeverBustPolicy(BasePolicy):
  '''
  A policy that never plays a move that can potentially bust, optimizing a simple metric
  that values potential outcomes according to a table
  '''
  def get_action(self, state):
    actions = self.game.actions(state)
    def eval_action(action):
      outcome = self.game.sim_place_cards(state, action)
      hands = [g.compute_hand(row) for row in state.rows]
      return g.compare_hands(hands[1], hands[0]) >= 0 and g.compare_hands(hands[2], hands[1]) >= 0
    evals = [(eval_action(action), action) for action in actions]
    viable = [y for x, y in evals if x == max(evals)[0]]
    return random.sample(viable, 1)[0]