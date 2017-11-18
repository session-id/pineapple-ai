from feature_extractors import *
from game import DECK_CARD_VALUES
import itertools

def tests():
	# Testing single / pair / triple
	features = feature_extractor_1(1, ['AC', '5C'], full_deck - set(['AC', '5C']), 10)
	assert features[('1', 'A')] == 1.0
	assert features[('1', '5')] == 1.0
	assert features[('2', 'A')] < 1.0
	assert features[('3', '4')] > 0.0
	assert features[('St', '5')] > 0.0
	assert features[('Fl', 'C')] > 0.0

full_deck = set([a + b for a, b in itertools.product(DECK_CARD_VALUES, 'CDHS')])
# precompute_hand_probs()
parse_probability_files()

tests()