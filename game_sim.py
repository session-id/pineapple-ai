from game import PineappleGame1
import policies

game = PineappleGame1()

def prompt_bool():
  return raw_input('(Y/N)? ').upper() == 'Y'

print "Play first?"
state = game.get_start_state(hero_first=prompt_bool())
policy = policies.HumanPolicy(game)

while not game.is_end(state):
  action = policy.get_action(state)
  state = game.get_random_outcome(state, action)

# Only for human policy
print "Final board:"
game.print_state(state)
print "Final utility:", game.utility(state)