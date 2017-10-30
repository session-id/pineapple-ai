import argparse

from game import PineappleGame1, BUST_PENALTY
import policies

parser = argparse.ArgumentParser(description='Simulate policy on pineapple.')
parser.add_argument('--num-games', type=int, default=1,
                    help='number of games to play')
parser.add_argument('--policy', type=str, default='human',
                    help='policy to use (human/random/baseline)')
parser.add_argument('--hero-first', action='store_true',
                    help='whether the hero goes first (default false)')
args = parser.parse_args()

policy_name_to_policy = {
  'human': policies.HumanPolicy,
  'baseline': policies.BaselinePolicy,
  'random': policies.RandomPolicy
}

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

game = PineappleGame1()

utilities = []
non_bust_utilities = []
busts = 0
for game_num in range(args.num_games):
  state = game.get_start_state(hero_first=args.hero_first)
  if args.policy not in policy_name_to_policy:
    raise RuntimeError('Unrecognized policy arg: {}'.format(args.policy))
  policy = policy_name_to_policy[args.policy](game, args)

  while not game.is_end(state):
    action = policy.get_action(state)
    state = game.get_random_outcome(state, action)

  if type(policy) == policies.HumanPolicy:
    print "Final board:"
    game.print_state(state)
  utility = game.utility(state)
  if utility == BUST_PENALTY:
    busts += 1
  else:
    non_bust_utilities += [utility]
  utilities += [utility]
  print "Game {} utility: {}".format(game_num, utility)

print "Average utility: {}".format(sum(utilities) / float(args.num_games))
print "Average non_bust_utilities: {}".format(sum(non_bust_utilities) / float(args.num_games))
print "Bust %: {} / {} = {}".format(busts, args.num_games, float(busts) / args.num_games)