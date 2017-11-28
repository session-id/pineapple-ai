import numpy as np
import random

import game as g
import hand_optimizer

game = g.PineappleGame1()

NUM_ITERS = 1000

utilities = []
for iter_num in xrange(NUM_ITERS):
  print "{:5} / {:5}".format(iter_num, NUM_ITERS), '\r',
  draw = random.sample(game.cards, 14)
  utilities += [hand_optimizer.optimize_hand([[], [], []], draw)]
print ''

utilities = np.array(utilities)
print "Average utility: {} +/- {}".format(np.mean(utilities), np.std(utilities) / np.sqrt(NUM_ITERS))