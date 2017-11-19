from collections import defaultdict
import random

import feature_extractors
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
  A policy that never plays a move that makes the current hierarchy of cards a bust. The policy
  randomly samples from all viable moves.
  '''
  def get_action(self, state):
    actions = self.game.actions(state)
    def eval_action(action):
      outcome = self.game.sim_place_cards(state, action)
      hands = [g.compute_hand(row) for row in outcome.rows]
      return g.compare_hands(hands[1], hands[0]) >= 0 and g.compare_hands(hands[2], hands[1]) >= 0
    evals = [(eval_action(action), action) for action in actions]
    viable = [y for x, y in evals if x == max(evals)[0]]
    return random.sample(viable, 1)[0]


class HeuristicNeverBustPolicy(BasePolicy):
  '''
  A policy that never plays a move that makes the current hierarchy of cards a bust. Within viable
  moves, it attempts to greedily form hands to maximize the total sum of hand values as denoted by
  a heuristic table.

  Afterwards, it tries to maximize the flexibility of the playable hand, which is the sum of the
  number of remaining slots per row raised to a preset power.
  '''
  def get_action(self, state):
    actions = self.game.actions(state)
    # Heuristic hand values
    self.hand_values = {
        '1': 0,
        '2': 1,
        '2+2': 2,
        '3': 4,
        'St': 8,
        'Fl': 8,
        '3+2': 12,
        '4': 20,
        'StFl': 30,
        'RoFl': 50  
      }
    def eval_action(action):
      outcome = self.game.sim_place_cards(state, action)
      hands = [g.compute_hand(row) for row in outcome.rows]
      total_value = sum(self.hand_values[hand[0]] for hand in hands)
      flexibility = sum([x ** 0.3 for x in self.game.get_remaining_capacities(outcome)])
      return (g.compare_hands(hands[1], hands[0]) >= 0 and g.compare_hands(hands[2], hands[1]) >= 0,
              total_value, flexibility)
    evals = [(eval_action(action), action) for action in actions]
    viable = [y for x, y in evals if x == max(evals)[0]]
    return random.sample(viable, 1)[0]


class RLPolicy(BasePolicy):
  '''
  Base class for all RL policies with incorporate_feedback.
  '''
  def incorporate_feedback(self, state, action, new_state):
    raise NotImplementedError


class QLearningPolicy(RLPolicy):
  '''
  A class that uses linear approximations of Q values built off of features to guide actions taken while
  learning optimal linear weights through feedback incorporation.
  '''
  def __init__(self, game, args):
    '''
    Input:
      game: Pineapple game instance
      feature_extractor: a function that extracts features from a given row. See feature_extractor.py for interface.
      exploration_prob: initial probability of exploration
    '''
    # Initialize step size, weight vector, etc
    # Add field to indicate whether training - this determines whether epsilon greedy policy is used
    super(QLearningPolicy, self).__init__(game, args)
    if args.feature_extractor == 'feature_extractor_1':
      self.feature_extractor = feature_extractors.feature_extractor_1
    else:
      raise RuntimeError("Feature extractor \"{}\" not found".format(args.feature_extractor))
    self.exploration_prob = args.exploration_prob
    self.train = True
    self.step_size = args.step_size
    self.weights = defaultdict(float)

  def get_step_size(self):
    return self.step_size

  def get_features(self, state, action):
    state = self.game.sim_place_cards(state, action)
    num_to_draw = self.game.num_to_draw(state)
    features = {}
    for row_num, cards in enumerate(state.rows):
      for k, v in self.feature_extractor(row_num, cards, state.remaining, num_to_draw).iteritems():
        features[(row_num, k)] = v
    return features

  def get_q(self, state, action):
    # Find exact solution if about to finish
    final_state = self.game.sim_place_cards(state, action)
    if self.game.is_end(final_state):
      return self.game.utility(final_state)
    # Otherwise use linear approximation
    features = self.get_features(state, action)
    return sum(self.weights[key] * features[key] for key in features)

  def get_action(self, state):
    actions = self.game.actions(state)
    if self.train and random.random() < self.exploration_prob:
      return random.choice(actions)
    return max((self.get_q(state, action), action) for action in actions)[1]

  def incorporate_feedback(self, state, action, new_state):
    if not self.train:
      return
    if self.game.is_end(new_state):
      return
    else:
      prediction = self.get_q(state, action)
      V_opt = max(self.get_q(new_state, a) for a in self.game.actions(new_state))
    features = self.get_features(state, action)
    deviation = prediction - V_opt
    for (name, value) in features.iteritems():
      self.weights[name] -= self.get_step_size() * deviation * value