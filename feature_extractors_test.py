from feature_extractors import *

def row_0_tests():
	# Testing single / pair / triple
	features = feature_extractor_1(0, ['AS', '4C'], ['AC', 'AH', 'AD'], 2)
	assert features[('1', 'A')] == 1.0
	assert features[('1', '4')] == 1.0
	assert features[('2', 'A')] == 1.0
	assert features[('3', '4')] == 0.0
	assert features[('St', '5')] == 0.0

	features = feature_extractor_1(0, ['4S', '4C'], ['AH', 'AD', '4D', '5C', '6D'], 3)
	assert features[('1', 'A')] > 0.0
	assert features[('1', '4')] == 1.0
	assert features[('2', '4')] == 1.0
	assert features[('2', 'A')] == 0.0
	assert features[('3', '4')] > 0.0

	features = feature_extractor_1(0, [], ['AH', 'AD', 'AC', '4D', '6C', '6D'], 3)
	assert features[('1', 'A')] > 0.0
	assert features[('1', '4')] > 0.0
	assert features[('2', '6')] > 0.0
	assert features[('2', '4')] == 0.0
	assert features[('3', 'A')] > 0.0

def last_two_row_tests():
	# Testing single / pair / triple / four fo a kind
	features = feature_extractor_1(1, ['AS', '4C'], ['AC', 'AH', 'AD'], 3)
	assert features[('1', 'A')] == 1.0
	assert features[('1', '4')] == 1.0
	assert features[('2', 'A')] == 1.0
	assert features[('4', 'A')] == 1.0
	assert features[('3', '4')] == 0.0
	assert features[('St', '5')] == 0.0

	features = feature_extractor_1(1, ['AS'], ['AH', 'AD', 'AC', '4D', '6C', '6D'], 4)
	assert features[('1', 'A')] == 1.0
	assert features[('1', '4')] > 0.0
	assert features[('2', '6')] > 0.0
	assert features[('2', '4')] == 0.0
	assert features[('3', 'A')] > 0.0
	assert features[('4', 'A')] > 0.0

	# Testing straight
	features = feature_extractor_1(1, ['2S', '4C'], ['AC', '2H', '3D', '4D', '5C', '6D'], 4)
	assert features[('2', '4')] > 0.0
	assert features[('2', 'A')] == 0.0
	assert features[('3', '4')] == 0.0
	assert features[('St', '5')] > 0.0
	assert features[('St', '6')] > 0.0
	assert features[('St', '7')] == 0.0

	features = feature_extractor_1(2, ['8D'], ['4C', '5H', '5S', '6D', '7S', '9D', 'TD', 'JC', 'QD', 'KS'], 5)
	assert features[('St', '8')] > 0.0
	assert features[('St', '9')] > 0.0
	assert features[('St', 'T')] > 0.0
	assert features[('St', 'J')] > 0.0
	assert features[('St', 'Q')] > 0.0
	assert features[('St', 'K')] == 0.0

	# Testing flush
	features = feature_extractor_1(2, ['8D', 'TD'], ['4D', '5D', '5C', '6D', '7D', '9D', 'JD', 'JC', 'QD', 'KS'], 5)
	assert features[('Fl', '8S')] == 0.0
	assert features[('Fl', 'AC')] == 0.0
	assert features[('Fl', 'KD')] == 0.0
	assert features[('Fl', 'JH')] == 0.0
	assert features[('Fl', 'TD')] > 0.0
	assert features[('Fl', 'QD')] > 0.0

	features = feature_extractor_1(2, ['8D', 'TS'], ['4D', '5D', '5C', '6D', '7D', '9D', 'JD', 'JC', 'QD', 'KS'], 5)
	assert features[('Fl', '8S')] == 0.0
	assert features[('Fl', 'AC')] == 0.0
	assert features[('Fl', 'KD')] == 0.0
	assert features[('Fl', 'JH')] == 0.0

	features = feature_extractor_1(2, ['5S', '7S', '8S'], ['4S', '5D', '5C', '6D', '9S', 'JD', 'JS', 'QD', 'KS', 'AS'], 4)
	assert features[('Fl', '8S')] == 0.0
	assert features[('Fl', 'AC')] == 0.0
	assert features[('Fl', 'KD')] == 0.0
	assert features[('Fl', '9S')] == 0.0
	assert features[('Fl', 'JS')] > 0.0
	assert features[('Fl', 'QS')] == 0.0
	assert features[('Fl', 'KS')] > 0.0
	assert features[('Fl', 'AS')] > 0.0

row_0_tests()
last_two_row_tests()