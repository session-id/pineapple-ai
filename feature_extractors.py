from collections import defaultdict
from game import DECK_CARD_VALUES, ROW_LENGTHS
import itertools
import numpy as np
import random

SUITS = 'CDHS'
DECK_SIZE = 52
CARDS_PER_VALUE = 4
CARDS_PER_SUIT = 13
MIN_DECK_SIZE = 22

card_to_value = dict() # relative ordering of cards (2 is lowest, A is highest)
probability_lookup_table = defaultdict(float)

# Converts an array into a map from array value to its count
def get_frequency_map(arr):
	freq = defaultdict(int)
	for val in arr:
		freq[val] += 1
	return freq

# Runs a monte carlo simulation of card drawings and averages the results
# over a set number of trials 
# Note: 'needed' parameter is typed depending on 'satisfies_hand' function
def monte_carlo_sim(deck, num_to_draw, satisfies_hand, needed):
	num_trials = 500
	success_cnt = 0
	for trial in range(num_trials):
		chosen_cards = random.sample(deck, num_to_draw)
		if (satisfies_hand(chosen_cards, needed)):
			success_cnt += 1
	return 1.0*success_cnt/num_trials


def precompute_hand_probs():
	for i, card in enumerate(DECK_CARD_VALUES):
		card_to_value[card] = i
	full_deck = set([a + b for a, b in itertools.product(DECK_CARD_VALUES, 'CDHS')])
	reference_card_values = ['A', '2', '3', '4' , '5'] # arbitrary values used to construct deck

	# Single / Pair / Triple / Four of a kind
	# probability_lookup_table -- key: (target_freq, row_freq, deck_freq, num_to_draw, deck_size)
	#								   all ints except for card_value (string)
	def satisfies_hand(chosen_cards, needed):
		card_value, num_cards_needed = needed
		chosen = [card[0] for card in chosen_cards]
		cnt = chosen.count(card_value)
		return (cnt >= num_cards_needed)

	print 'head'
	
	output_file = open('cardinality_probabilities.txt', 'w')
	parameters = ['Probability', 'Target freq', 'Row freq', 'Deck freq', 'Number to draw', 'Deck size']
	output_file.write('\t'.join(parameters) + '\n')
	
	card_value = reference_card_values[0] 
	for row_freq in range(ROW_LENGTHS[1] + 1):
		deck_freq = CARDS_PER_VALUE - row_freq
		for deck_size in range(MIN_DECK_SIZE, DECK_SIZE + 1):
			# Build customized deck
			deck = full_deck.copy()
			deck -= set([a + b for a, b in itertools.product(card_value, 'CDHS')])
			deck = set(list(deck)[:(deck_size - deck_freq)])
			for i in range(deck_freq):
				deck.add(card_value + SUITS[i])

			for num_to_draw in range(sum(ROW_LENGTHS) + 1):
				for target_freq in range(1, 5):
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

					probability_lookup_table[(target_freq, row_freq, deck_freq, num_to_draw, deck_size)] = prob
					output_file.write('\t'.join([str(x).rjust(9) for x in [prob, target_freq, row_freq, deck_freq, num_to_draw, deck_size]]) + '\n')
	output_file.close()

	print 'straight'

	# Straight
	# probability_lookup_table -- key: (sorted_multiplicity, num_to_draw, deck_size)
	#								   (tuple, int, int)
	def satisfies_straight(chosen_cards, needed):
		chosen = set(card[0] for card in chosen_cards)
		for val in needed:
			if (val not in chosen):
				return False
		return True

	output_file = open('straight_probabilities.txt', 'w')
	parameters = ['probability', 'multiplicity', 'num_to_draw', 'deck_size']
	output_file.write('\t'.join(parameters) + '\n')

	for num_empty_space in range(ROW_LENGTHS[1], 0, -1):
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

				for num_to_draw in range(num_empty_space, sum(ROW_LENGTHS) + 1):
					prob = monte_carlo_sim(deck, num_to_draw, satisfies_straight, set(needed))
					probability_lookup_table[(multiplicity, num_to_draw, deck_size)] = prob
					output_file.write('\t'.join([str(x).rjust(10) for x in [prob, multiplicity, num_to_draw, deck_size]]) + '\n')
	output_file.close()

	print 'Flush'

	# Flush
	# probability_lookup_table -- key: (high_card, in_cards, num_empty_space, num_suit_left, num_to_draw, deck_size)
	#								   all ints except for high_Card (string) and in_cards (bool) which indicates whether high card is in row
	def satisfies_flush(chosen_cards, needed):
		chosen_card_values = [DECK_CARD_VALUES.index(card[0]) for card in chosen_cards]
		chosen_card_suits = [card[1] for card in chosen_cards]
		sorted_suits = [x for _,x in sorted(zip(chosen_card_values, chosen_card_suits))]
		feature_value, num_cards_needed, high_card_in_cards = needed
		high_card_name = feature_value[0]
		high_card_value = card_to_value[high_card_name]
		flush_suit = feature_value[1]
		high_card = high_card_name + flush_suit

		if (chosen_card_suits.count(flush_suit) < num_cards_needed):
			return False
		if (high_card_in_cards):
			helper_arr = chosen_card_values + [high_card_value]
			idx = sorted(helper_arr).index(high_card_value)
			if (sorted_suits[:idx].count(flush_suit) < num_cards_needed):
				return False
		elif (high_card not in chosen_cards):
			return False
		else:
			idx = sorted(chosen_card_values).index(high_card_value)
			if ((sorted_suits[:idx]).count(flush_suit) < num_cards_needed):
				return False
		return True

	output_file = open('flush_probabilities.txt', 'w')
	parameters = ['probability', 'high_card', 'in_cards', 'num_empty_space', 'num_suit_left', 'num_to_draw', 'deck_size']
	output_file.write('\t    '.join(parameters) + '\n')

	reference_suit = 'C'
	for num_empty_space in range(1, ROW_LENGTHS[1] + 1):
		for num_suit_left in range(num_empty_space, CARDS_PER_SUIT + 1):
			for deck_size in range(MIN_DECK_SIZE, DECK_SIZE + 1):
				for high_card in DECK_CARD_VALUES[3:]: # min high card value of '5'
					feature_value = high_card + reference_suit
					needed = (feature_value, num_empty_space)
					for in_cards in range(2): # False or True
						# Build customized deck
						deck = full_deck.copy()
						deck -= set([a + b for a, b in itertools.product(reference_card_values[-num_suit_left:], 'C')])
						deck = set(list(deck)[:(deck_size - num_suit_left)])
						valid_card_values = DECK_CARD_VALUES
						if (in_cards):
							valid_card_values = valid_card_values.replace(high_card, '')
							valid_card_values = list(valid_card_values[ROW_LENGTHS[1] - num_empty_space - 1:])
						else:
							valid_card_values = list(valid_card_values[ROW_LENGTHS[1] - num_empty_space:])
						card_combinations = [a + b for a, b in itertools.product(np.random.choice(valid_card_values, num_suit_left), reference_suit)]
						deck |= set(card_combinations)
						
						for num_to_draw in range(num_empty_space, sum(ROW_LENGTHS) + 1):
							prob = monte_carlo_sim(deck, num_to_draw, satisfies_flush, needed + (in_cards,))
							probability_lookup_table[(high_card, in_cards, num_empty_space, num_suit_left, num_to_draw, deck_size)] = prob
							output_file.write('\t'.join([str(x).rjust(13) for x in [prob, high_card, in_cards, num_empty_space, num_suit_left, num_to_draw, deck_size]]) + '\n')
	output_file.close()

# Returns a monte-carlo simulated hand probability feature vector of a given row
# Inputs:
#	row_num 	[int]: row number
#	cards 		[set]: set of cards in the given row
#	deck 		[set]: set of remaining cards in the form 4S (4 of spades), AC (ace of clubs), etc.
#	num_to_draw [int]: remaining number of cards to drow
# Output:
# 	Return defaultdict with keys named according to hand
#	Key: 	(hand_name, card_value); hand_name = ['1', '2', '3', '4', 'St', 'Fl'], 
#									 card_value = '23456789TJQKA' (with/without suit 'CDHS')
#			- card_value of 'St' (straight) based on high card
#			- card_value of 'Fl' (flush) based on high card and suit (i.e. 'AS' or '7C')
#	Value: 	probability of hand_name at card_value 
def feature_extractor_1(row_num, cards, deck, num_to_draw):
	features = defaultdict(float)
	row_card_freq = get_frequency_map([card[0] for card in cards])
	deck_card_freq = get_frequency_map([card[0] for card in deck])
	num_cards = len(cards)
	num_empty_space = ROW_LENGTHS[row_num] - num_cards
	deck_size = len(deck)
	assert(num_to_draw >= num_empty_space)

	# Single / Pair / Triple / Four of a kind
	for card_value in DECK_CARD_VALUES:
		row_freq = row_card_freq[card_value]
		deck_freq = deck_card_freq[card_value]
		assert(deck_freq + row_freq == 4) 
		for target_freq in range(1, 5):
			if (target_freq == 4 and row_num == 0): 
				continue

			features[(str(target_freq), card_value)] = \
				probability_lookup_table[(target_freq, row_freq, deck_freq, num_to_draw, deck_size)]

	# Straight / Flush
	if (row_num > 0):
		def get_multiplicity(deck_card_freq, needed):
			multiplicity = []
			for needed_card in needed:
				multiplicity.append(deck_card_freq[needed_card])
			return tuple(sorted(multiplicity))

		# Straight
		card_values = [DECK_CARD_VALUES.index(card[0]) for card in cards]
		card_suits = [card[1] for card in cards]
		max_value = max(card_values)
		min_value = min(card_values)

		# Checks for A-5 straight possibility
		def firstStraight(card_values):
			for val in card_values:
				if (val > card_to_value['5'] and val < card_to_value['A']):
					return False
			return True

		if (firstStraight(card_values)):
			needed = []
			for i in range(card_to_value['2'], card_to_value['5'] + 1):
				if (i not in card_values):
					needed.append(i)
			if (card_to_value['A'] not in card_values): # Ace
				needed.append(card_to_value['A'])
			multiplicity = get_multiplicity(deck_card_freq, needed)
			features[('St', '5')] = probability_lookup_table[(multiplicity, num_to_draw, deck_size)]

		if (max_value - min_value < 5):
			for high_card in range(max(max_value, card_to_value['6']), min(min_value + 5, card_to_value['A'] + 1)):
				needed = []
				for i in range(high_card - 4, high_card + 1):
					if (i not in card_values):
						needed.append(i)
				multiplicity = get_multiplicity(deck_card_freq, needed)
				features[('St', DECK_CARD_VALUES[high_card])] = probability_lookup_table[(multiplicity, num_to_draw, deck_size)]

		# Flush
		for suit in SUITS:
			deck_suits = [card[1] for card in deck]
			deck_suit_count = deck_suits.count(suit)
			if (card_suits.count(suit) == num_cards):
				for card_name in DECK_CARD_VALUES:
					if (card_to_value[card_name] < max_value):
						continue
					feature_value = card_name + suit
					in_cards = (card_name in cards)
					num_cards_needed = ROW_LENGTHS[row_num] - num_cards
					features[('Fl', feature_value)] = probability_lookup_table[(card_name, in_cards, num_cards_needed, deck_suit_count, num_to_draw, deck_size)]

	return features


