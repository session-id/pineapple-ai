class HumanPolicy:
  def __init__(self, game):
    self.game = game

  def get_action(self, state):
    while True:
      self.game.print_state(state)
      try:
        # Action input format is Card1 Pos1 Card2 Pos2 ... CardN PosN
        inp = raw_input("Action (space separated, case insensitive): ").upper()
        inp = inp.split(' ')
        action = sorted(tuple((inp[i], int(inp[i+1])) for i in range(0, len(inp), 2)))
        new_state = self.game.get_random_outcome(state, action) # Check if valid
        return action
      except Exception as e:
        print 'Invalid action: {}'.format(e)