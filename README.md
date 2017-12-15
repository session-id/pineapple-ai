# pineapple-ai
AI for playing the game pineapple

## Helper files

``feature_extractors.py``: contains different feature extractors that work on either states or state, action pairs

``game.py``: contains the core logic of the Pineapple game, as well as helper functions for dealing with cards and hands

``hand_optimizer.py``: contains the CSP solvers that solve for the best possible ending hand given remaining draw and, in the adversarial case, a distribution of opponent hands

``policies.py``: contains the code implementing the various policies we used to play the game

## Fantasyland Simulator

The file ``fantasyland.py`` was used to determine the value in royalties earned on average in Fantasyland, and also to determine the Royalties Per Hand of our Oracle. Running on 14 cards simulates fantasyland, while 17 cards simulates oracle.

```
python fantasyland.py --num-games 10000 --num-cards [14 or 17]
```

## Solitaire Pineapple AI

The file ```game_sim.py``` runs specified policies over the specified number of games. For policies that require training, like the Q-learning policy, a number of training games can be specified as well.

```
python game_sim.py --num-train 0 --num-test 1000 --policy [random, baseline, heuristic_neverbust, oracle_eval, vs_oracle_eval] --num-oracle-sims 20

python game_sim.py --num-train 1000 --num-test 1000 --policy q_learning --feature_extractor feature_extractor_3 --step-size 0.005 --exploration-prob 0.1
```

## Two Player Pineapple Game

The file ```adversarial_game_sim.py``` plays two policies against each other and reports statistics on how the policies performed against each other. All flags used to specify solitaire Pineapple AI's can be used to play those AI's in this version of the game as well. Additional arguments include the number of fantasyland simulations to run (used to determine the value of fantasyland against a particular opponent startegy) as well as the number of opponent simulations to perform in the adversarial Oracle Eval policy.

Example run (the one used to evaluate non-adversarial Oracle Eval against adversarial Oracle Eval in the paper):

```
python adversarial_game_sim.py --num-train 0 --num-test 1000 --player-policy vs_oracle_eval --opp-policy adv_vs_oracle_eval --num-opp-sims 20 --num-fl-sims 100 --log-file temp.log
```