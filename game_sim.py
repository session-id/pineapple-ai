import argparse
import numpy as np

from game import PineappleGame1, BUST_PENALTY
import policies

parser = argparse.ArgumentParser(description='Simulate policy on pineapple.')
parser.add_argument('--num-train', type=int, default=0,
                    help='number of games to train policy on')
parser.add_argument('--num-test', type=int, default=1,
                    help='number of games to test policy on')
parser.add_argument('--policy', type=str, default='human',
                    help='policy to use (human/random/baseline/neverbust/heuristic_neverbust/q_learning)')
parser.add_argument('--hero-first', action='store_true',
                    help='whether the hero goes first (default false)')
parser.add_argument('--print-util-freq', type=int, default=-1,
                    help='how frequently to print average utilities')
parser.add_argument('--verbose', action='store_true',
                    help='whether to print all states and actions')
parser.add_argument('--exploration-prob', type=float, default=0.2,
                    help='for RL policies, probability of exploration')
parser.add_argument('--step-size', type=float, default=0.1,
                    help='step size for learning policies through gradient descent')
parser.add_argument('--feature-extractor', type=str, default='feature_extractor_1',
                    help='feature extractor to use (feature_extractor_1)')
args = parser.parse_args()

policy_name_to_policy = {
  'human': policies.HumanPolicy,
  'baseline': policies.BaselinePolicy,
  'random': policies.RandomPolicy,
  'neverbust': policies.NeverBustPolicy,
  'heuristic_neverbust': policies.HeuristicNeverBustPolicy,
  'q_learning': policies.QLearningPolicy
}

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

game = PineappleGame1()

utilities = []
non_bust_utilities = []
busts = 0
if args.policy not in policy_name_to_policy:
  raise RuntimeError('Unrecognized policy arg: {}'.format(args.policy))
policy = policy_name_to_policy[args.policy](game, args)
if type(policy) == policies.HumanPolicy:
  args.print_util_freq = 1

for game_num in range(args.num_test + args.num_train):
  # No exploration during testing
  if game_num == args.num_train:
    print "Training ended. Now testing:"
    policy.exploration_prob = 0
    
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
    if utility == BUST_PENALTY:
      busts += 1
    else:
      non_bust_utilities += [utility]
    utilities += [utility]

    if type(policy) == policies.HumanPolicy:
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

utilities = np.array(utilities)
np.save('utilities', utilities)
game_num += 1

print "\n"
print "Average utility: {} +/- {}".format(np.mean(utilities), np.std(utilities) / np.sqrt(game_num))
print "Average non_bust_utilities: {}".format(sum(non_bust_utilities) / float(game_num))
print "Bust %: {} / {} = {}".format(busts, game_num, float(busts) / game_num)