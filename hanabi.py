from pprint import pprint
from random import shuffle

NUM_PLAYERS = 3
HAND_SIZE = 5
COLORS = ['pink', 'blue', 'white', 'yellow', 'green']
MAX_CLUES = 8


class Game:
    def __init__(self):
        self.game_over = False
        self.remaining_fuses = 3
        self.remaining_clues = 8
        self.whose_turn = 0
        self.last_turn = -1
        self.deck = []
        self.graveyard = []
        self.table = {color: [] for color in COLORS}


class Card(object):

    def __init__(self, color, number):
        self.color = color
        self.number = number

    def __repr__(self):
        return "%s %s" % (self.color, self.number)


class Player:

    def __init__(self):
        self.hand = [None] * HAND_SIZE
        self.knowledge = [dict([('color', None), ('number', None)]) for i in xrange(0, HAND_SIZE)]

    def lose_card(self, index):
        lost = self.hand[index]
        self.hand[index] = game.deck.pop()
        self.knowledge[index] = {'color': None, 'number': None}
        return lost

    def play_card(self, index):
        played = self.lose_card(index)

        print "Playing %r" % played

        if len(game.table[played.color]) == 0 and played.number == 1:
            game.table[played.color].append(played)
        elif len(game.table[played.color]) > 0 and game.table[played.color][-1].number == played.number - 1:
            game.table[played.color].append(played)
        else:
            game.graveyard.append(played)
            game.remaining_fuses -= 1

    def discard(self, index):
        discarded = self.lose_card(index)

        print "Discarding %r" % discarded

        game.remaining_clues = min(game.remaining_clues + 1, MAX_CLUES)
        game.graveyard.append(discarded)

    def receive_clue(self, clue):
        game.remaining_clues -= 1
        clue_type = 'number' if type(clue) == int else 'color'
        for index, card in enumerate(self.hand):
            if getattr(card, clue_type) == clue:
                print "%d matches" % index
                self.knowledge[index][clue_type] = clue


# Build deck
game = Game()
for color in COLORS:
    for i in xrange(0, 3):
        game.deck.append(Card(color, 1))
    for i in xrange(2, 5):
        game.deck.append(Card(color, i))
        game.deck.append(Card(color, i))
    game.deck.append(Card(color, 5))
shuffle(game.deck)

# Deal initial hands
players = [Player() for i in xrange(0, NUM_PLAYERS)]
for player in players:
    for i in xrange(0, HAND_SIZE):
        player.hand[i] = game.deck.pop()
    print player.hand

# Main loop
while not game.game_over:
    current_player = players[game.whose_turn]
    if game.remaining_clues > 0:
        players[0].receive_clue('pink')
        print players[0].knowledge
    else:
        current_player.play_card(0)
    pprint(game.table)

    #if game isn't over, prepare for next turn
    if game.remaining_fuses > 0 and game.last_turn < NUM_PLAYERS:
        if len(game.deck) > 0:
            game.whose_turn = (game.whose_turn + 1) % NUM_PLAYERS
        else:
            game.last_turn += 1
            game.whose_turn = (game.whose_turn + 1) % NUM_PLAYERS
    else:
        game.game_over = True
