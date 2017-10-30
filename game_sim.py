from game import PineappleGame1

game = PineappleGame1()

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

print "Play first?"
state = game.get_start_state(hero_first=prompt_bool())

while not game.is_end(state):
  game.print_state(state)
  try:
    # Action input format is Card1 Pos1 Card2 Pos2 ... CardN PosN
    inp = raw_input("Action (space separated, case insensitive): ").upper()
    inp = inp.split(' ')
    action = sorted(tuple((inp[i], int(inp[i+1])) for i in range(0, len(inp), 2)))
    state = game.get_random_outcome(state, action)
  except Exception as e:
    print 'Invalid action: {}'.format(e)

print "Final utility:", game.utility(state)