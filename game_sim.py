import argparse
import numpy as np
import json

from game import PineappleGame1, BUST_PENALTY, FANTASYLAND_BONUS, FANTASYLAND_WORTH
import policies

parser = argparse.ArgumentParser(description='Simulate policy on pineapple.')
parser.add_argument('--num-train', type=int, default=0,
                    help='number of games to train policy on')
parser.add_argument('--num-test', type=int, default=1,
                    help='number of games to test policy on')
parser.add_argument('--policy', type=str, default='human',
                    help='policy to use (human/random/baseline/neverbust/heuristic_neverbust/q_learning/oracle_eval'
                         '/q_learning2/vs_oracle_eval)')
parser.add_argument('--hero-first', action='store_true',
                    help='whether the hero goes first (default false)')
parser.add_argument('--print-util-freq', type=int, default=-1,
                    help='how frequently to print average utilities')
parser.add_argument('--verbose', action='store_true',
                    help='whether to print all states and actions')
parser.add_argument('--exploration-prob', type=float, default=0.2,
                    help='for RL policies, probability of exploration')
parser.add_argument('--step-size', type=float, default=0.01,
                    help='step size for learning policies through gradient descent')
parser.add_argument('--feature-extractor', type=str, default='feature_extractor_1',
                    help='feature extractor to use (feature_extractor_1/2/3). note: some feature extractors can only be used'
                    'with q_learning2 (those that ingest state, action)')
parser.add_argument('--num-oracle-sims', type=int, default=3,
                    help='number of simulations for oracle_eval to run per action result')
parser.add_argument('--oracle-outcome-weighting', type=float, default=1.0,
                    help='exponent for how outcomes are weighted for the oracle')
parser.add_argument('--distinguish-draws', action='store_true',
                    help='for feature extraction, whether to consider every num_to_draw differently')
args = parser.parse_args()

policy_name_to_policy = {
  'human': policies.HumanPolicy,
  'baseline': policies.BaselinePolicy,
  'random': policies.RandomPolicy,
  'neverbust': policies.NeverBustPolicy,
  'heuristic_neverbust': policies.HeuristicNeverBustPolicy,
  'q_learning': policies.QLearningPolicy,
  'oracle_eval': policies.OracleEvalPolicy,
  'vs_oracle_eval': policies.VarSimOracleEvalPolicy,
  'q_learning2': policies.QLearningPolicy2
}

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

game = PineappleGame1()

utilities = []
non_bust_utilities = []
busts = 0
fantasylands = 0
if args.policy not in policy_name_to_policy:
  raise RuntimeError('Unrecognized policy arg: {}'.format(args.policy))
policy = policy_name_to_policy[args.policy](game, args)
if type(policy) == policies.HumanPolicy:
  args.print_util_freq = 1

for game_num in range(args.num_test + args.num_train):
  # No exploration during testing
  if game_num == args.num_train:
    print "Training ended. Now testing:"
    policy.train = False
    
  try:
    state = game.get_start_state(hero_first=args.hero_first)

    while not game.is_end(state):
      if args.verbose:
        game.print_state(state)
      action = policy.get_action(state)
      if args.verbose:
        print "Action:", action
      new_state = game.get_random_outcome(state, action)
      if isinstance(policy, policies.RLPolicy):
        policy.incorporate_feedback(state, action, new_state)
      state = new_state

    utility = game.utility(state)
    utilities += [utility]
    if game.is_fantasyland(state):
      fantasylands += 1
      utility -= FANTASYLAND_BONUS # For calculation below
    if game_num >= args.num_train:
      if utility == BUST_PENALTY:
        busts += 1
        non_bust_utilities += [0.]
      else:
        non_bust_utilities += [utility]

    if args.verbose or type(policy) == policies.HumanPolicy:
      print "Final board:"
      game.print_state(state)

    if args.print_util_freq != -1:
      if (game_num + 1) % args.print_util_freq == 0:
        start_game = game_num - args.print_util_freq + 1
        avg_utility = sum(utilities[start_game:]) / float(args.print_util_freq)
        print "Games {:4} -{:4} average utility: {}".format(start_game, game_num, avg_utility)
    else:
      print "Game {:4} / {:4}\r".format(game_num+1, args.num_test),

    if type(policy) == policies.HumanPolicy:
      print "\n"
  # keyboard interrupt breaks early
  except KeyboardInterrupt as e:
    game_num -= 1
    break

if isinstance(policy, policies.RLPolicy):
  try:
    with open('weights.json', 'w') as fp:
      json.dump(policy.weights, fp, sort_keys=True, indent=2, separators=(',', ': '))
  except Exception:
    pass

utilities = np.array(utilities)
non_bust_utilities = np.array(non_bust_utilities)
np.save('utilities', utilities)
utilities = utilities[args.num_train:]
game_num += 1
num_test_played = game_num - args.num_train

fl = float(fantasylands) / num_test_played
fl_std = np.sqrt(fl * (1 - fl) / num_test_played)
u = np.mean(non_bust_utilities)
u_std = np.std(non_bust_utilities) / np.sqrt(num_test_played)
num_std = np.sqrt(u_std ** 2 + (FANTASYLAND_WORTH * fl_std) ** 2)
denom_std = fl_std
num = u + FANTASYLAND_WORTH * fl
denom = 1 + fl
rph = num / denom
rph_std = num / denom * np.sqrt((num_std / num) ** 2 + (denom_std / denom) ** 2)

print "\n"
print "Average utility: {} +/- {}".format(np.mean(utilities), np.std(utilities) / np.sqrt(num_test_played))
print "Royalties per hand: {} +/- {}".format(rph, rph_std)
print "Bust %: {} / {} = {}".format(busts, game_num, float(busts) / (num_test_played))
print "Fantasyland %: {} / {} = {}".format(fantasylands, game_num, float(fantasylands) / (num_test_played))