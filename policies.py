from collections import defaultdict
import math
import numpy as np
import random

import feature_extractors
import game as g
import hand_optimizer

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
    self.feature_extractor = feature_extractors.name_to_extractor(args.feature_extractor)
    self.distinguish_draws = args.distinguish_draws
    self.exploration_prob = args.exploration_prob
    self.train = True
    self.step_size = args.step_size
    self.weights = defaultdict(float)
    feature_extractors.parse_probability_files()

  def get_step_size(self):
    return self.step_size

  def get_features(self, state, action):
    state = self.game.sim_place_cards(state, action)
    num_to_draw = self.game.num_to_draw(state)
    features = {}
    for row_num, cards in enumerate(state.rows):
      for k, v in self.feature_extractor(row_num, cards, state.remaining, num_to_draw).iteritems():
        if self.distinguish_draws:
          features[(num_to_draw, row_num, k)] = v
        else:
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
    total_update = 0
    for (name, value) in features.iteritems():
      self.weights[name] -= self.get_step_size() * deviation * value
      total_update += abs(self.get_step_size() * deviation * value)
    # print "Total update:", total_update, "Deviation:", deviation, "len(features):", len(features) #,


class QLearningPolicy2(QLearningPolicy):
  '''
  A version of QLearningPolicy above that uses feature extractors that work on generic state, action
  pairs.
  '''
  def __init__(self, game, args):
    super(QLearningPolicy2, self).__init__(game, args)
    self.feature_extractor = self.feature_extractor(self.game)
    self.weights = self.feature_extractor.default_weights()

  def get_features(self, state, action):
    return self.feature_extractor.extract(state, action)


class OracleEvalPolicy(BasePolicy):
  '''
  A policy that uses the oracle best case royalties averaged over several draws to optimize the
  current action.
  '''
  def __init__(self, game, args):
    super(OracleEvalPolicy, self).__init__(game, args)
    self.num_sims = args.num_oracle_sims
    self.alpha = args.oracle_outcome_weighting

  def get_action(self, state):
    actions = self.game.actions(state)
    def eval_action(action):
      outcome = self.game.sim_place_cards(state, action)
      values = []
      if self.game.num_to_draw(outcome) == 0:
        return self.game.utility(outcome)
      num_to_draw_map = {12: 8, 9: 6, 6: 5, 3: 3}
      # num_to_draw = int(math.ceil(self.game.num_to_draw(outcome) * 0.7))
      num_to_draw = num_to_draw_map[self.game.num_to_draw(outcome)]
      num_sims = self.num_sims
      for _ in xrange(self.num_sims):
        draw = random.sample(outcome.remaining, num_to_draw)
        values += [hand_optimizer.optimize_hand(outcome.rows, draw)]
      values = np.array(values)
      return (np.mean(np.sign(values) * np.abs(values) ** self.alpha)) ** (1. / self.alpha)
    eval_actions = [(eval_action(action), action) for action in actions]
    # print "Estimated value: {}".format(max(eval_actions)[0])
    return max(eval_actions)[1]


class VarSimOracleEvalPolicy(BasePolicy):
  '''
  OracleEvalPolicy with a different exploration policy that explores the best actions in greater depth.
  '''
  def __init__(self, game, args):
    super(VarSimOracleEvalPolicy, self).__init__(game, args)
    self.num_sims = args.num_oracle_sims

  def get_action(self, state):
    actions = self.game.actions(state)
    outcomes = [(self.game.sim_place_cards(state, action), action) for action in actions]
    num_to_draw_map = {12: 8, 9: 6, 6: 5, 3: 3, 0: 0}

    def interpolate_action(prev, outcome, num_sims, round_num):
      values = []
      num_to_draw = num_to_draw_map[self.game.num_to_draw(outcome)]
      for _ in xrange(num_sims):
        draw = random.sample(outcome.remaining, num_to_draw)
        values += [hand_optimizer.optimize_hand(outcome.rows, draw)]
      values = np.array(values)
      return prev * (1 - 1. / round_num) + np.mean(values) / round_num

    outcomes_with_histories = [(0., outcome, action) for outcome, action in outcomes]
    round_num = 1.
    while len(outcomes_with_histories) > 1:
      outcomes_with_histories = [(interpolate_action(prev, outcome, self.num_sims, round_num), outcome, action)
                                  for prev, outcome, action in outcomes_with_histories]
      outcomes_with_histories.sort()
      outcomes_with_histories = outcomes_with_histories[len(outcomes_with_histories) / 2:]
      round_num += 1
    return outcomes_with_histories[0][2]


class TDLearningPolicy(RLPolicy):
  '''
  A class that uses linear approximations of Value functions built off of features to guide actions taken while
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
    super(TDLearningPolicy, self).__init__(game, args)
    self.feature_extractor = feature_extractors.name_to_extractor(args.feature_extractor)
    self.exploration_prob = args.exploration_prob
    self.train = True
    self.step_size = args.step_size
    self.weights = defaultdict(float)
    feature_extractors.parse_probability_files()

  def get_step_size(self):
    return self.step_size

  def get_features(self, state, action):
    pass

  def get_q(self, state, action):
    pass

  def get_action(self, state):
    pass

  def incorporate_feedback(self, state, action, new_state):
    pass

'''
Adversarial capable policies below
'''

class AdvVarSimOracleEvalPolicy(BasePolicy):
  '''
  Adversarial version of VarSimOracleEvalPolicy
  '''
  def __init__(self, game, args):
    super(AdvVarSimOracleEvalPolicy, self).__init__(game, args)
    self.num_sims = args.num_oracle_sims
    self.num_opp_sims = args.num_opp_sims

  def get_action(self, state):
    actions = self.game.actions(state)
    outcomes = [(self.game.sim_place_cards(state, action), action) for action in actions]
    num_to_draw = self.game.num_to_draw(outcomes[0][0])
    table = {0: 17, 5: 12, 7: 9, 9: 6, 11: 3, 13: 0}
    opp_num_to_draw = table[sum(len(x) for x in state.opp_rows)]
    opp_rows = state.opp_rows

    # TODO: Better adversarial fantasyland bonus calculation

    opp_num_to_draw_map = {12: 8, 9: 6, 6: 5, 3: 3, 0: 0}
    if opp_num_to_draw <= 9:
      opp_combos = []
      if opp_num_to_draw > 0:
        num_to_draw_sim = opp_num_to_draw_map[opp_num_to_draw]
        for _ in xrange(self.num_opp_sims):
          # state.remaining and outcome.remaining for any outcome should be equal
          draw = random.sample(state.remaining, num_to_draw_sim)
          # Assume opponent just plays to maximize their royalties
          value, combo = hand_optimizer.optimize_hand(opp_rows, draw, return_combo=True)
          opp_combos += [combo]
      else:
        opp_combos = [[g.compute_hand(cards) for cards in opp_rows]]
      value_fn = lambda rows, draw: hand_optimizer.optimize_hand_adv(rows, draw, opp_combos)
    else:
      value_fn = lambda rows, draw: hand_optimizer.optimize_hand(rows, draw)

    num_to_draw_map = {12: 8, 9: 6, 6: 5, 3: 3, 0: 0}

    def interpolate_action(prev, outcome, num_sims, round_num):
      values = []
      num_to_draw_sim = num_to_draw_map[num_to_draw]
      for _ in xrange(num_sims):
        draw = random.sample(outcome.remaining, num_to_draw_sim)
        values += [value_fn(outcome.rows, draw)]
      values = np.array(values)
      return prev * (1 - 1. / round_num) + np.mean(values) / round_num

    outcomes_with_histories = [(0., outcome, action) for outcome, action in outcomes]
    round_num = 1.
    while len(outcomes_with_histories) > 1:
      outcomes_with_histories = [(interpolate_action(prev, outcome, self.num_sims, round_num), outcome, action)
                                  for prev, outcome, action in outcomes_with_histories]
      outcomes_with_histories.sort()
      outcomes_with_histories = outcomes_with_histories[len(outcomes_with_histories) / 2:]
      round_num += 1
    return outcomes_with_histories[0][2]
