from hand_optimizer import *

import time

# Testing

# print possible_hands(['TH', '9H'], 1, ['2H', '2S', 'JC', 'QC', '8C', '7H', 'AH'])
# print possible_hands(['TH', '5S'], 1, ['2H', '2S', 'JC', '8C', '7H', '9D', '5C', '5D'])
# print possible_hands([], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH', 'TC', 'TD', '8S', '8H'])
# print possible_hands(['TD', 'TS'], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])
# print possible_hands(['TD', 'TS', '3C', 'QD'], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])
# print possible_hands(['TD', 'TS', 'QS', 'QD'], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])
# print possible_hands(['TD', 'TS', 'TC'], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH'])
# print possible_hands([], 0, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH', 'JS', '7C'])
# print possible_hands([], 0, ['2H', '2C', 'JH', 'JD', 'JS'])
# print possible_hands([], 2, ['2H', '2C', 'JH', 'JD', 'JS'])
# print possible_hands([], 1, ['2H', '3S', '4C', '5C', '7H', 'TH', 'JH', 'QH', 'JS', '7C', '9H', 'AH', 'KH'])
# print possible_hands([], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH', 'JS', '7C', '9H', 'AH', 'KH'])

# start = time.time()
# for _ in xrange(1000):
#   #possible_hands([], 1, ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH', 'TC', 'TD', '8S', '8H'])
#   optimize_hand([['TH', 'TC'], ['2H', '2D', '3S', '4C'], ['7S', '8S', '9S', 'TS']], ['TD', 'JC', 'QS', '2C', '3C', '4D'])
# print "Average time for possible_hands: {}".format((time.time() - start) / 1000.)

# print optimize_hand([['TH', 'TC'], ['2H', '2D', '3S', '4C'], ['8S', '9S', 'TS']], ['7S', '7D', 'TD', 'JC', 'QS', '2C', '3C', '4D'])
# print optimize_hand([['TH', 'TC'], ['2H', '2D', '3S', '4C'], ['8S', '8C', 'TS']], ['7S', '7D', 'TD', 'JC', 'QS', '2C', '3C', '4D', '8H', 'TH'])
# print optimize_hand([['TC'], ['2H', '2D', '3S', '4C'], ['8S', '8C', 'TS']], ['7S', '7D', 'TD', 'JC', 'QS', '2C', '3C', '4D', '8H', 'TH', '8D'], True)
# print optimize_hand([['TC', 'AH'], ['2H', '2D', '3S', '4C'], ['8S', '8C', 'TS', 'TD', '8D']], ['TH', 'AS', 'AC'], True)
# print optimize_hand([['AC', 'AD', 'AS'], ['7D'], []], ['2H', '2S', 'JC', '8C', '7H', 'TH', 'JH', 'QH', 'JS', '7C', '9H', 'AH', 'KH'], True)