from game import *

game = PineappleGame1()

def ranking_test():
  flush = compute_hand(['2H', '3H', '5H', '6H', 'KH'])
  king_high = compute_hand(['2H', '3H', '5H', '6H', 'KS'])
  straight = compute_hand(['2H', '3H', '5H', '6H', '4C'])
  triple = compute_hand(['5D', '5S', '5H', '4H', 'AC'])
  wheel = compute_hand(['2H', '3H', '5H', 'AH', '4C'])
  straight_flush = compute_hand(['2H', '3H', '5H', 'AH', '4H'])
  worse_king_high = compute_hand(['2H', '3H', '4H', '6H', 'KS'])
  two_pair = compute_hand(['2H', '2D', 'AH', '6H', '6C'])
  worse_two_pair = compute_hand(['2H', '2D', 'KD', '6H', '6C'])
  quad = compute_hand(['5C', '5S', '5H', 'AH', '5D'])
  full_house = compute_hand(['5C', '5S', '5H', 'AH', 'AD'])
  pair = compute_hand(['2H', '2D', 'AH', '6H', '7C'])

  def compare_test(hand1, hand2):
    #print hand1, 'vs', hand2, ':', compare_hands(hand1, hand2)
    return compare_hands(hand1, hand2)

  assert compare_test(flush, king_high) == 1
  assert compare_test(king_high, flush) == -1
  assert compare_test(wheel, straight) == -1
  assert compare_test(straight_flush, triple) == 1
  assert compare_test(triple, king_high) == 1
  assert compare_test(wheel, wheel) == 0
  assert compare_test(worse_king_high, king_high) == -1
  assert compare_test(two_pair, worse_two_pair) == 1
  assert compare_test(two_pair, two_pair) == 0
  assert compare_test(straight_flush, quad) == 1
  assert compare_test(quad, full_house) == 1
  assert compare_test(full_house, flush) == 1
  assert compare_test(flush, straight) == 1
  assert compare_test(straight, triple) == 1
  assert compare_test(triple, two_pair) == 1
  assert compare_test(two_pair, pair) == 1
  assert compare_test(pair, king_high) == 1

  print "Ranking test passed!"

ranking_test()