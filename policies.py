import random

from game import card_value

class BasePolicy:
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
  Policy that randomly chooses an action.
  '''

  def get_action(self, state):
    actions = self.game.actions(state)
    return random.sample(actions, 1)[0]

class BaselinePolicy(BasePolicy):
  '''
  Baseline policy as described in project proposal.
  '''

  def get_action(self, state):
    remaining_capacities = self.game.get_remaining_capacities(state)
    draw = sorted(state.draw, lambda x, y: card_value(y) - card_value(x))
    values = [card_value(card) for card in draw]
    raise NotImplementedError