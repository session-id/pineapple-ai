from collections import defaultdict
from game import DECK_CARD_VALUES, ROW_LENGTHS
import random


SUITS = 'CDHS'
card_to_value = dict() # relative ordering of cards (2 is lowest, A is highest)

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
	card_freq = get_frequency_map([card[0] for card in cards])
	for i, card in enumerate(DECK_CARD_VALUES):
		card_to_value[card] = i
	num_cards = len(cards)
	num_cards_left = ROW_LENGTHS[row_num] - num_cards
	assert(num_to_draw >= num_cards_left)

	# Single / Pair / Triple / Four of a kind
	def satisfies_hand(chosen_cards, needed):
		card_value, num_cards_needed = needed
		chosen = [card[0] for card in chosen_cards]
		cnt = chosen.count(card_value)
		return (cnt >= num_cards_needed)

	for card_value in DECK_CARD_VALUES:
		freq = card_freq[card_value]
		for target_freq in range(1, 5):
			if (target_freq == 4 and row_num == 0): 
				continue

			if (freq >= target_freq):
				prob = 1.0
			else:
				num_cards_needed = target_freq - freq
				if (num_cards_needed > num_cards_left): 
					continue
				needed = (card_value, num_cards_needed)
				prob = monte_carlo_sim(deck, num_to_draw, satisfies_hand, needed)

			features[(str(target_freq), card_value)] = prob

	# Straight / Flush
	if (row_num > 0):
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

		def satisfies_straight(chosen_cards, needed):
			chosen = [card_to_value[card[0]] for card in chosen_cards]
			for val in needed:
				if (val not in chosen):
					return False
			return True

		if (firstStraight(card_values)):
			needed = []
			for i in range(card_to_value['2'], card_to_value['5'] + 1):
				if (i not in card_values):
					needed.append(i)
			if (card_to_value['A'] not in card_values): # Ace
				needed.append(card_to_value['A'])
			features[('St', '5')] = monte_carlo_sim(deck, num_to_draw, satisfies_straight, needed)

		if (max_value - min_value < 5):
			for high_card in range(max(max_value, card_to_value['6']), min(min_value + 5, card_to_value['A'] + 1)):
				needed = []
				for i in range(high_card - 4, high_card + 1):
					if (i not in card_values):
						needed.append(i)
				features[('St', DECK_CARD_VALUES[high_card])] = monte_carlo_sim(deck, num_to_draw, satisfies_straight, needed)

		# Flush
		for suit in SUITS:
			if (card_suits.count(suit) == num_cards):
				for card_name in DECK_CARD_VALUES:
					if (card_to_value[card_name] < max_value):
						continue
					num_cards_needed = ROW_LENGTHS[row_num] - num_cards
					feature_value = card_name + suit
					needed = (feature_value, num_cards_needed)

					def satisfies_flush(chosen_cards, needed):
						chosen_card_values = [DECK_CARD_VALUES.index(card[0]) for card in chosen_cards]
						chosen_card_suits = [card[1] for card in chosen_cards]
						sorted_suits = [x for _,x in sorted(zip(chosen_card_values, chosen_card_suits))]
						feature_value, num_cards_needed = needed
						high_card_name = feature_value[0]
						high_card_value = card_to_value[high_card_name]
						flush_suit = feature_value[1]
						high_card = high_card_name + flush_suit

						if (chosen_card_suits.count(flush_suit) < num_cards_needed):
							return False
						if (high_card in cards):
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

					features[('Fl', feature_value)] = monte_carlo_sim(deck, num_to_draw, satisfies_flush, needed)

	return features


