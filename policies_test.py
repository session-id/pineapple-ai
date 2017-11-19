from argparse import Namespace

import game as g
import policies

'''
Q Learning policy
'''

def test_feature_extractor(row_num, cards, deck, num_to_draw):
  return {'row_num': row_num, 'num_to_draw': num_to_draw}

game = g.PineappleGame1()
args = Namespace()
args.feature_extractor = 'feature_extractor_1'
args.exploration_prob = 0.2
policy = policies.QLearningPolicy(game, args)
assert policy.exploration_prob == 0.2
policy.feature_extractor = test_feature_extractor
policy.weight[(1, 'row_num')] = -1
policy.weight[(2, 'num_to_draw')] = 2
state = game.get_start_state(False)
action = game.actions(state)[100]
assert policy.get_q(state, action) == -1 + 2 * 12

state2 = g.PineappleGame1State([['AH', 'AC', '2S'], ['3H', '3D', '4H', '4D'], ['7C', '7D', '8C', '8D']], ['KH', 'KS', 'KD'], state.remaining)
action = game.actions(state2)[0]
# Should get ace royalties
assert policy.get_q(state2, action) == 9