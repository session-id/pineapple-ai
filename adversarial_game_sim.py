import argparse
import copy
import json
import numpy as np
import random
import time

from game import PineappleGame1, PineappleGame2, BUST_PENALTY, FANTASYLAND_BONUS, FANTASYLAND_WORTH, NUM_FANTASYLAND_DRAW
import game as g
import hand_optimizer
import policies

parser = argparse.ArgumentParser(description='Simulate policy on pineapple.')
parser.add_argument('--num-train', type=int, default=0,
                    help='number of games to train policy on')
parser.add_argument('--num-test', type=int, default=1,
                    help='number of games to test policy on')
parser.add_argument('--player-policy', type=str, default='human',
                    help='policy to use (human/random/baseline/neverbust/heuristic_neverbust/q_learning/oracle_eval'
                         '/q_learning2/vs_oracle_eval/adv_vs_oracle_eval)')
parser.add_argument('--opp-policy', type=str, default='human',
                    help='policy to use (human/random/baseline/neverbust/heuristic_neverbust/q_learning/oracle_eval'
                         '/q_learning2/vs_oracle_eval)')
# parser.add_argument('--hero-first', action='store_true',
#                     help='whether the hero goes first (default false)')
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
parser.add_argument('--num-opp-sims', type=int, default=10,
                    help='number of opponent simulations to do for MC adversarial policies')
parser.add_argument('--num-fl-sims', type=int, default=100,
                    help='number of fantasyland simulations to do')
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
  'adv_vs_oracle_eval': policies.AdvVarSimOracleEvalPolicy,
  'q_learning2': policies.QLearningPolicy2
}

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

start_time = time.time()

player_game = PineappleGame2('player')
opp_game = PineappleGame2('opponent')

player_utilities = []
player_non_bust_utilities = [] # Essentially royalties
player_busts = 0
player_fantasylands = 0
player_final_hands = []

opp_utilities = []
opp_non_bust_utilities = [] # Essentially royalties
opp_busts = 0
opp_fantasylands = 0
opp_final_hands = []

if args.player_policy not in policy_name_to_policy:
  raise RuntimeError('Unrecognized policy arg: {}'.format(args.player_policy))
if args.opp_policy not in policy_name_to_policy:
  raise RuntimeError('Unrecognized policy arg: {}'.format(args.opp_policy))
player_policy = policy_name_to_policy[args.player_policy](player_game, args)
opp_policy = policy_name_to_policy[args.opp_policy](opp_game, args)
if type(player_policy) == policies.HumanPolicy:
  args.print_util_freq = 1

for game_num in range(args.num_test + args.num_train):
  # No exploration during testing
  if game_num == args.num_train:
    print "Training ended. Now testing:"
    player_policy.train = False
    opp_policy.train = False
    
  try:
    player_state, opp_state = player_game.get_start_state()

    while not player_game.is_end(player_state):
      def take_action(game, state, opp_state, policy):
        # if args.verbose:
        #   game.print_state(state)
        action_state = copy.deepcopy(state)
        action_state.remaining = state.fake_remaining
        action = policy.get_action(action_state)
        # if args.verbose:
        #   print "Action:", action
        new_state = game.get_outcome(state, action, opp_state)
        if isinstance(policy, policies.RLPolicy):
          policy.incorporate_feedback(state, action, new_state)
        return new_state

      player_state = take_action(player_game, player_state, opp_state, player_policy)
      opp_state = take_action(opp_game, opp_state, player_state, opp_policy)

    player_utility = player_game.utility(player_state)
    player_royalties = player_game.royalties_for_hand(player_state)
    opp_utility = opp_game.utility(opp_state)
    opp_royalties = opp_game.royalties_for_hand(opp_state)

    player_utilities += [player_utility]
    if player_game.is_fantasyland(player_state):
      player_fantasylands += 1
    if game_num >= args.num_train:
      if player_game.is_bust(player_state):
        player_busts += 1
      player_non_bust_utilities += [player_royalties]
      player_final_hands += [g.rows_to_hands(player_state.rows)]

    opp_utilities += [opp_utility]
    if opp_game.is_fantasyland(opp_state):
      opp_fantasylands += 1
    if game_num >= args.num_train:
      if opp_game.is_bust(opp_state):
        opp_busts += 1
      opp_non_bust_utilities += [opp_royalties]
      opp_final_hands += [g.rows_to_hands(player_state.rows)]

    if args.verbose or type(player_policy) is policies.HumanPolicy or type(opp_policy) is policies.HumanPolicy:
      print player_game.name, "\'s Final board:"
      player_game.print_state(player_state)

    if args.print_util_freq != -1:
      if (game_num + 1) % args.print_util_freq == 0:
        start_game = game_num - args.print_util_freq + 1
        player_avg_utility = sum(player_utilities[start_game:]) / float(args.print_util_freq)
        opp_avg_utility = sum(opp_utilities[start_game:]) / float(args.print_util_freq)
        print "Player games {:4} -{:4} average utility: {}".format(start_game, game_num, player_avg_utility)
    else:
      print "Game {:4} / {:4}\r".format(game_num+1, args.num_test),

    if type(player_policy) == policies.HumanPolicy or type(opp_policy) == policies.HumanPolicy:
      print "\n"
  # keyboard interrupt breaks early
  except KeyboardInterrupt as e:
    game_num -= 1
    break

print "\n"

# Simulates effect of fantasyland by averaging over multiple fantasyland configurations and final
# configurations for the opponent found during simulation.

# Note: The current version overestimates the performance of players against fantasyland since their
# hands were created with knowledge of opponent draws.
fl_train_cutoff = len(player_final_hands) / 2
opp_fl_utilities = []
player_fl_utilities = []
opp_fl_worths = []
player_fl_worths = []
try:
  for fl_sim_num in xrange(args.num_fl_sims):
    print "Performing FL sim {:4} / {:4}\r".format(fl_sim_num + 1, args.num_fl_sims),
    draw = random.sample(player_game.cards, NUM_FANTASYLAND_DRAW)

    # Optimize vs player
    # TODO: make hand_optimizer return an actual set of rows making the best hand
    worth, fl_combo = hand_optimizer.optimize_hand_adv([[], [], []], draw, player_final_hands[:fl_train_cutoff],
      return_combo=True, fl_bonus=False)
    opp_fl_worths += [worth]
    fl_hands = hand_optimizer.combo_to_hand(fl_combo)
    # TODO: remove code duplication with utility calculation
    for player_hands in player_final_hands[fl_train_cutoff:]:
      opp_fl_utilities += [g.adv_utility(fl_hands, player_hands)]

    # Optimize vs opp
    worth, fl_combo = hand_optimizer.optimize_hand_adv([[], [], []], draw, opp_final_hands[:fl_train_cutoff],
      return_combo=True, fl_bonus=False)
    player_fl_worths += [worth]
    fl_hands = hand_optimizer.combo_to_hand(fl_combo)
    for opp_hands in opp_final_hands[fl_train_cutoff:]:
      player_fl_utilities += [g.adv_utility(fl_hands, opp_hands)]
except KeyboardInterrupt:
  pass

opp_fl_utilities = np.array(opp_fl_utilities)
player_fl_utilities = np.array(player_fl_utilities)
player_fl_worths = np.array(player_fl_worths)
opp_fl_worths = np.array(opp_fl_worths)

print ""

def print_stats(name, utilities, non_bust_utilities, game_num, busts, fantasylands, fl_utilities,
    fl_worths, opp_fantasylands, opp_fl_utilities):
  utilities = np.array(utilities)
  non_bust_utilities = np.array(non_bust_utilities)
  np.save('utilities', utilities)
  utilities = utilities[args.num_train:]
  game_num += 1
  num_test_played = game_num - args.num_train

  fl = float(fantasylands) / num_test_played
  fl_std = np.sqrt(fl * (1 - fl) / num_test_played)
  opp_fl = float(opp_fantasylands) / num_test_played
  opp_fl_std = np.sqrt(opp_fl * (1 - opp_fl) / num_test_played)
  fl_util = np.mean(fl_utilities)
  fl_util_std = np.std(fl_utilities) / np.sqrt(num_test_played)
  opp_fl_util = np.mean(opp_fl_utilities)
  opp_fl_util_std = np.std(opp_fl_utilities) / np.sqrt(num_test_played)

  # Utility computation
  u = np.mean(utilities)
  u_std = np.mean(utilities) / np.sqrt(num_test_played)
  denom = (1 + fl) * (1 + opp_fl)
  denom_std = denom * np.sqrt((fl_std / (1 + fl)) ** 2 + (opp_fl_std / (1 + opp_fl)) ** 2)
  num = u + fl * fl_util - opp_fl * opp_fl_util
  num_std = np.sqrt(u_std ** 2 + (fl * fl_util_std) ** 2 + (fl_std * fl_util) ** 2\
    + (opp_fl * opp_fl_util_std) ** 2 + (opp_fl_std * opp_fl_util) ** 2)
  avg_util = num / denom
  avg_util_std = num / denom * np.sqrt((num_std / num) ** 2 + (denom_std / denom) ** 2)

  # RPH computation
  fl_worth = np.mean(fl_worths)
  fl_worth_std = np.std(fl_worths) / np.sqrt(num_test_played)
  r = np.mean(non_bust_utilities)
  r_std = np.std(non_bust_utilities) / np.sqrt(num_test_played)
  num_std = np.sqrt(r_std ** 2 + (fl_worth * fl_std) ** 2 + (fl_worth_std * fl) ** 2)
  denom_std = fl_std
  num = r + fl_worth * fl
  denom = 1 + fl
  rph = num / denom
  rph_std = num / denom * np.sqrt((num_std / num) ** 2 + (denom_std / denom) ** 2)

  bust = float(busts) / num_test_played
  bust_std = np.sqrt(bust * (1 - bust) / num_test_played)

  print "\n", name
  print "Average utility: {} +/- {}".format(avg_util, avg_util_std)
  print "Non_fl utility: {} +/- {}".format(u, u_std)
  print "Royalties per hand: {} +/- {}".format(rph, rph_std)
  print "Bust %: {} / {} = {} +/- {}".format(busts, game_num, bust, bust_std)
  print "Fantasyland %: {} / {} = {} +/- {}".format(fantasylands, game_num, fl, fl_std)
  print "Fantasyland utility: {} +/- {}".format(fl_util, fl_util_std)

print_stats(player_game.name, player_utilities, player_non_bust_utilities, game_num, player_busts, player_fantasylands,
  player_fl_utilities, player_fl_worths, opp_fantasylands, opp_fl_utilities)
print_stats(opp_game.name, opp_utilities, opp_non_bust_utilities, game_num, opp_busts, opp_fantasylands,
  opp_fl_utilities, opp_fl_worths, player_fantasylands, player_fl_utilities)

print "\nTook {} seconds.".format(time.time() - start_time)

