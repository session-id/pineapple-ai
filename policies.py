import random

from game import card_value

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
        # Action input format is Card1 Pos1 Card2 Pos2 ... CardN PosN
        inp = raw_input("Action (space separated, case insensitive): ").upper()
        inp = inp.split(' ')
        action = sorted(tuple((inp[i], int(inp[i+1])) for i in range(0, len(inp), 2)))
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
    draw = sorted(state.draw, lambda x, y: card_value(y) - card_value(x))
    assert len(draw) == 5 or len(draw) == 3
    # Always take highest 2 cards
    if len(draw) == 3:
      draw = draw[:-1]
    values = [card_value(card) for card in draw]

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