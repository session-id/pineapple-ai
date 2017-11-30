from collections import defaultdict
import itertools
import numpy as np
import random

import hand_optimizer
from game import DECK_CARD_VALUES, ROW_LENGTHS

def name_to_extractor(name):
	d = {
		'feature_extractor_1': feature_extractor_1,
		'feature_extractor_2': feature_extractor_2,
		'feature_extractor_3': FeatureExtractor3
	}
	if name not in d:
		raise RuntimeError("Feature extractor \"{}\" not found".format(name))
	return d[name]

'''
Constants
'''

SUITS = 'CDHS'
DECK_SIZE = 52
CARDS_PER_VALUE = 4
CARDS_PER_SUIT = 13
MIN_DECK_SIZE = 18
TOTAL_CARDS_SEEN = 17

'''
File names
'''

CARDINALITY_PROBABLITIES_FILE = 'cardinality_probabilities.txt'
STRAIGHT_PROBABILITIES_FILE = 'straight_probabilities.txt'
FLUSH_PROBABILITIES_FILE = 'flush_probabilities.txt'

'''
Global variables
'''

card_to_value = {v:k for k, v in enumerate(DECK_CARD_VALUES)} # relative ordering of cards (2 is lowest, A is highest)
probability_lookup_table = defaultdict(float) # all keys are tuples of strings, all values are floats

# For comparison between rows
proxy_hand_score = defaultdict(float, {
	'1':0,
	'2':2,
	'3':10,
	'St':15,
	'Fl':20,
	'4':50,
})

### Converts an array into a map from array value to its count
def get_frequency_map(arr):
	freq = defaultdict(int)
	for val in arr:
		freq[val] += 1
	return freq

### Runs a monte carlo simulation of card drawings and averages the results
### over a set number of trials 
### Note: 'needed' parameter is typed depending on 'satisfies_hand' function
def monte_carlo_sim(deck, num_to_draw, satisfies_hand, needed):
	num_trials = 500
	success_cnt = 0
	for trial in range(num_trials):
		chosen_cards = random.sample(deck, num_to_draw)
		if (satisfies_hand(chosen_cards, needed)):
			success_cnt += 1
	return 1.0*success_cnt/num_trials

### Precomputes all hand probabilities and outputs to three files
def precompute_hand_probs():
	raise Exception("Comment this line out if you REALLY want to precompute all probabilities again. Otherwise call parse_probability_files :)")

	for i, card in enumerate(DECK_CARD_VALUES):
		card_to_value[card] = i
	full_deck = set([a + b for a, b in itertools.product(DECK_CARD_VALUES, 'CDHS')])
	reference_card_values = ['A', '2', '3', '4' , '5'] # arbitrary values used to construct deck

	# Single / Pair / Triple / Four of a kind
	# probability_lookup_table -- key: (target_freq, row_freq, deck_freq, num_to_draw, deck_size)
	def satisfies_hand(chosen_cards, needed):
		card_value, num_cards_needed = needed
		chosen = [card[0] for card in chosen_cards]
		cnt = chosen.count(card_value)
		return (cnt >= num_cards_needed)

	print 'Normal'

	output_file = open(CARDINALITY_PROBABLITIES_FILE, 'w')
	parameters = ['Probability', 'Target freq', 'Row freq', 'Deck freq', 'Number to draw', 'Deck size']
	output_file.write('\t'.join(parameters) + '\n')
	
	card_value = reference_card_values[0] 
	for target_freq in range(1, 5):
		for row_freq in range(CARDS_PER_VALUE):
			for deck_freq in range(CARDS_PER_VALUE - row_freq + 1):
				for deck_size in range(MIN_DECK_SIZE, DECK_SIZE + 1):
					# Build customized deck
					if (target_freq > row_freq):
						deck = full_deck.copy()
						deck -= set([a + b for a, b in itertools.product(card_value, 'CDHS')])
						deck = set(list(deck)[:(deck_size - deck_freq)])
						for i in range(deck_freq):
							deck.add(card_value + SUITS[i])
					for num_to_draw in range(min(deck_size, TOTAL_CARDS_SEEN) + 1):
						if (row_freq >= target_freq):
							prob = 1.0
						elif (num_to_draw == 0):
							prob = 0.0
						else:
							num_cards_needed = target_freq - row_freq
							if (num_cards_needed > deck_freq): 
								continue
							needed = (card_value, num_cards_needed)
							prob = monte_carlo_sim(deck, num_to_draw, satisfies_hand, needed)
						key = tuple([str(x) for x in [target_freq, row_freq, deck_freq, num_to_draw, deck_size]])
						probability_lookup_table[key] = prob
						output_file.write('\t'.join([str(x).rjust(9) for x in [prob, target_freq, row_freq, deck_freq, num_to_draw, deck_size]]) + '\n')
	output_file.close()

	print 'Straight'

	# Straight
	# probability_lookup_table -- key: ('St', sorted_multiplicity, num_to_draw, deck_size)
	def satisfies_straight(chosen_cards, needed):
		chosen = set(card[0] for card in chosen_cards)
		for val in needed:
			if (val not in chosen):
				return False
		return True

	output_file = open(STRAIGHT_PROBABILITIES_FILE, 'w')
	parameters = ['probability', 'multiplicity', 'num_to_draw', 'deck_size']
	output_file.write('\t'.join(parameters) + '\n')

	for num_empty_space in range(ROW_LENGTHS[1], -1, -1):
		possibilities = []
		for i in range(1, 5):
			for j in range(num_empty_space):
				possibilities.append(i)
		multiplicities = set(itertools.combinations(possibilities, num_empty_space))
		for multiplicity in multiplicities:
			deck_freq = sum(multiplicity)
			for deck_size in range(MIN_DECK_SIZE, DECK_SIZE + 1):
				# Build customized deck
				deck = full_deck.copy()
				deck -= set([a + b for a, b in itertools.product(reference_card_values[:num_empty_space], 'CDHS')])
				deck = set(list(deck)[:(deck_size - deck_freq)])	
				needed = []
				for idx in range(len(multiplicity)):
					val = multiplicity[idx]
					for suit_idx in range(val):
						deck.add(reference_card_values[idx] + SUITS[suit_idx])
					needed.append(reference_card_values[idx])

				for num_to_draw in range(num_empty_space, min(deck_size, TOTAL_CARDS_SEEN) + 1):
					prob = monte_carlo_sim(deck, num_to_draw, satisfies_straight, set(needed))
					key = tuple([str(x) for x in ['St', multiplicity, num_to_draw, deck_size]])
					probability_lookup_table[key] = prob
					output_file.write('\t'.join([str(x).rjust(10) for x in [prob, multiplicity, num_to_draw, deck_size]]) + '\n')
	output_file.close()

	print 'Flush'

	# Flush
	# probability_lookup_table -- key: ('Fl', num_empty_space, num_suit_left, num_to_draw, deck_size)
	def satisfies_flush(chosen_cards, needed):
		chosen_card_suits = [card[1] for card in chosen_cards]
		flush_suit, num_cards_needed = needed
		return (chosen_card_suits.count(flush_suit) >= num_cards_needed)

	output_file = open(FLUSH_PROBABILITIES_FILE, 'w')
	parameters = ['probability', 'num_empty_space', 'num_suit_left', 'num_to_draw', 'deck_size']
	output_file.write('\t'.join(parameters) + '\n')

	reference_suit = 'C'
	for num_empty_space in range(1, ROW_LENGTHS[1] + 1):
		for num_suit_left in range(num_empty_space, CARDS_PER_SUIT + 1):
			for deck_size in range(MIN_DECK_SIZE, DECK_SIZE + 1):
				# Build customized deck
				deck = full_deck.copy()
				deck -= set([a + b for a, b in itertools.product(DECK_CARD_VALUES, reference_suit)])
				deck = set(list(deck)[:(deck_size - num_suit_left)])
				deck |= set([a + b for a, b in itertools.product(DECK_CARD_VALUES[:num_suit_left], reference_suit)])
				needed = (reference_suit, num_empty_space)
				for num_to_draw in range(num_empty_space, min(deck_size, TOTAL_CARDS_SEEN) + 1):
					prob = monte_carlo_sim(deck, num_to_draw, satisfies_flush, needed)
					key = tuple([str(x) for x in ['Fl', num_empty_space, num_suit_left, num_to_draw, deck_size]])
					probability_lookup_table[key] = prob
					output_file.write('\t'.join([str(x).rjust(13) for x in [prob, num_empty_space, num_suit_left, num_to_draw, deck_size]]) + '\n')
	output_file.close()


### Call this function to read precomputed probabilities from corresponding files.
### All probabilities are stored in probability_lookup_table.
def parse_probability_files():
	with open(CARDINALITY_PROBABLITIES_FILE) as cf:
		cf.readline()
		for line in cf:
			line = [x.strip() for x in line.strip().split('\t')]
			probability_lookup_table[tuple(line[1:])] = float(line[0])

	with open(STRAIGHT_PROBABILITIES_FILE) as sf:
		sf.readline()
		hand_name = ['St']
		for line in sf:
			line = [x.strip() for x in line.strip().split('\t')]
			probability_lookup_table[tuple(hand_name + line[1:])] = float(line[0])

	with open(FLUSH_PROBABILITIES_FILE) as ff:
		ff.readline()
		hand_name = ['Fl']
		for line in ff:
			line = [x.strip() for x in line.strip().split('\t')]
			probability_lookup_table[tuple(hand_name + line[1:])] = float(line[0])


### Returns a monte-carlo simulated hand probability feature vector of a given row
### Inputs:
###		row_num 	[int]: row number
###		cards 		[set]: set of cards in the given row
###		deck 		[set]: set of remaining cards in the form 4S (4 of spades), AC (ace of clubs), etc.
###		num_to_draw [int]: remaining number of cards to drow
### Output:
### 	Return defaultdict with key-value pairs as follows
###
###		Key: 	(hand_name, card_value); hand_name = ['1', '2', '3', '4', 'St', 'Fl'], 
###										 card_value = '23456789TJQKA' (with/without suit 'CDHS')
###				- card_value of 'St' (straight) based on high card
###				- card_value of 'Fl' (flush) based on high card and suit (i.e. 'AS' or '7C')
###		Value: 	probability of hand_name at card_value 
def feature_extractor_1(row_num, cards, deck, num_to_draw):
	features = defaultdict(float)
	row_card_freq = get_frequency_map([card[0] for card in cards])
	deck_card_freq = get_frequency_map([card[0] for card in deck])
	num_cards = len(cards)
	num_empty_space = ROW_LENGTHS[row_num] - num_cards
	deck_size = len(deck)
	assert(num_to_draw >= num_empty_space)

	### Single / Pair / Triple / Four of a kind
	for card_value in DECK_CARD_VALUES:
		row_freq = row_card_freq[card_value]
		deck_freq = deck_card_freq[card_value]
		for target_freq in range(1, 5):
			if (target_freq == 4 and row_num == 0 or num_empty_space < target_freq - row_freq): 
				continue
			key = tuple([str(x) for x in [target_freq, row_freq, deck_freq, num_to_draw, deck_size]])
			features[(str(target_freq), card_value)] = probability_lookup_table[key]
	
	### Straight / Flush
	if (row_num > 0):
		### Straight

		# Returns a sorted list of multiplicities of each needed card
		def get_multiplicity(deck_card_freq, needed):
			multiplicity = []
			for val in needed:
				needed_card = DECK_CARD_VALUES[val]
				multiplicity.append(deck_card_freq[needed_card])
			return tuple(sorted(multiplicity))

		# Populates value for first straight feature
		def get_first_straight_feature():
			needed = []
			for i in range(card_to_value['2'], card_to_value['5'] + 1):
				if (i not in card_values):
					needed.append(i)
			if (card_to_value['A'] not in card_values): # Ace
				needed.append(card_to_value['A'])
			multiplicity = get_multiplicity(deck_card_freq, needed)
			key = tuple(str(x) for x in ['St', multiplicity, num_to_draw, deck_size])
			features[('St', '5')] = probability_lookup_table[key]

		# Checks for A-5 straight possibility
		def first_straight(card_values):
			for val in card_values:
				if (val > card_to_value['5'] and val < card_to_value['A']):
					return False
			return True

		card_values = [DECK_CARD_VALUES.index(card[0]) for card in cards]
		card_suits = [card[1] for card in cards]

		if (len(cards) == 0):
			get_first_straight_feature()
			for high_card in range(card_to_value['6'], card_to_value['A'] + 1):
				needed = [i for i in range(high_card - 4, high_card + 1)]
				multiplicity = get_multiplicity(deck_card_freq, needed)
				key = tuple(str(x) for x in ['St', multiplicity, num_to_draw, deck_size])
				features[('St', DECK_CARD_VALUES[high_card])] = probability_lookup_table[key]
		else:
			max_value = max(card_values)
			min_value = min(card_values)

			if (first_straight(card_values)):
				get_first_straight_feature()

			if (max_value - min_value < 5):
				for high_card in range(max(max_value, card_to_value['6']), min(min_value + 5, card_to_value['A'] + 1)):
					needed = []
					for i in range(high_card - 4, high_card + 1):
						if (i not in card_values):
							needed.append(i)
					multiplicity = get_multiplicity(deck_card_freq, needed)
					key = tuple(str(x) for x in ['St', multiplicity, num_to_draw, deck_size])
					features[('St', DECK_CARD_VALUES[high_card])] = probability_lookup_table[key]

		### Flush
		for suit in SUITS:
			deck_suits = [card[1] for card in deck]
			deck_suit_count = deck_suits.count(suit)
			if (card_suits.count(suit) == num_cards):
				num_cards_needed = ROW_LENGTHS[row_num] - num_cards
				key = tuple([str(x) for x in ['Fl', num_cards_needed, deck_suit_count, num_to_draw, deck_size]])
				features[('Fl', suit)] = probability_lookup_table[key]

	return features


# Feature_extractor_1 with additional information derived from input parameters
def feature_extractor_2(row_num, cards, deck, num_to_draw):
	features = feature_extractor_1(row_num, cards, deck, num_to_draw)
	features[('Row Len', len(cards))] = 1
	features[('Num To Draw', num_to_draw)] = 1
	return features

### Feature Extractor compares the expected "score" of 2 rows, adjusted for card rank
### Inputs:
###		row_1, row_2		[int]: row numbers
###		cards_1, cards_2 	[set]: sets of cards in the given row
###		deck 				[set]: set of remaining cards in the form 4S (4 of spades), AC (ace of clubs), etc.
###		num_to_draw 		[int]: remaining number of cards to draw
### Output:
### 	Return : 			[int]: 1 if row_1 has a higher expected score than row_2, else 0
def feature_extractor_3a(row_1, row_2, cards_1, cards_2, deck, num_to_draw):

	prob_1 = feature_extractor_1(row_1, cards_1, deck, num_to_draw)
	EV_1 = sum([prob_1[x]*proxy_hand_score[x] for x in proxy_hand_score]) + sum([card_to_value[x] for i,x in cards_1])/100

	prob_2 = feature_extractor_1(row_2, cards_2, deck, num_to_draw)
	EV_2 = sum([prob_2[x]*proxy_hand_score[x] for x in proxy_hand_score]) + sum([card_to_value[x] for i,x in cards_2])/100

	return 1 if (EV_1 > EV_2) else 0

### Feature Extractor compares the expected "score" of 2 rows, adjusted for card rank
### Inputs:
###		cardset				[array]: array of sets = [cards_1, cards_2, cards_3]
###		deck 				[set]: set of remaining cards in the form 4S (4 of spades), AC (ace of clubs), etc.
###		num_to_draw 		[int]: remaining number of cards to draw
### Output:
### 	Return : 			[defaultdict(int)]: {(1,2): int, (2,3): int} where output[(m,n)] = 1 if EV_m > EV_n
def feature_extractor_3(cardset, deck, num_to_draw):

	return defaultdict(int, {
			(1,2): feature_extractor_3a(1,2, cardset[1], cardset[2], deck, num_to_draw),
			(2,3): feature_extractor_3a(2,3, cardset[2], cardset[3], deck, num_to_draw)
		})


class FeatureExtractor(object):
	def __init__(self, game):
		self.game = game

	def default_weights(self):
		return defaultdict(float)


# An oracle based feature extractor
class FeatureExtractor3(FeatureExtractor):
	def default_weights(self):
		return defaultdict(float, {
				(3, 3): 1.0,
				(6, 4): 0.25,
				(6, 5): 0.5,
				(6, 6): 0.25,
				(9, 6): 0.25,
				(9, 7): 0.5,
				(9, 8): 0.15,
				(9, 9): 0.1,
				(12, 8): 0.2,
				(12, 9): 0.5,
				(12, 10): 0.15,
				(12, 11): 0.1,
				(12, 12): 0.05,
			})

	def extract(self, state, action):
		state = self.game.sim_place_cards(state, action)
		num_to_draw = self.game.num_to_draw(state)
		ranges_and_sims = {
			3: ([3], 20),
			6: ([4, 5, 6], 8),
			9: ([6, 7, 8, 9], 3),
			12: ([8, 9, 10, 11, 12], 2)
		}
		features = {}
		draw_range, num_sims = ranges_and_sims[num_to_draw]
		for num_to_draw2 in draw_range:
			total = 0.
			for _ in xrange(num_sims):
				draw = random.sample(state.remaining, num_to_draw2)
				total += hand_optimizer.optimize_hand(state.rows, draw)
			features[(num_to_draw, num_to_draw2)] = total / float(num_sims)
		return features