import argparse
import numpy as np
import random

import game as g
import hand_optimizer

parser = argparse.ArgumentParser(description='Simulate fantasyland like situations.')
parser.add_argument('--num-games', type=int, default=1000,
                    help='number of games to play')
parser.add_argument('--num-cards', type=int, default=14,
                    help='number of cards to be dealt')

args = parser.parse_args()

game = g.PineappleGame1()

utilities = []
for iter_num in xrange(args.num_games):
  print "{:5} / {:5}".format(iter_num, args.num_games), '\r',
  draw = random.sample(game.cards, args.num_cards)
  utilities += [hand_optimizer.optimize_hand([[], [], []], draw)]
print ''

utilities = np.array(utilities)
print "Average utility: {} +/- {}".format(np.mean(utilities), np.std(utilities) / np.sqrt(args.num_games))