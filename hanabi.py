from __future__ import division
from pprint import pprint
import random
import sys

NUM_PLAYERS = 3
HAND_SIZE = 5
COLORS = ['pink', 'blue', 'white', 'yellow', 'green']
CARD_COUNTS = {1: 3, 2: 2, 3: 2, 4: 2, 5:1}
MAX_CLUES = 8
NUMBER_OF_GAMES = 50
# Current 50 Game Average Score: 11.980000 *without last turn*


class Game:
    
    def __init__(self):
        self.game_over = False
        self.remaining_fuses = 3
        self.remaining_clues = 8
        self.whose_turn = 0
        self.last_turn = -1
        self.deck = []
        self.graveyard = []
        self.turn_taken = False
        self.table = {color: [] for color in COLORS}

        for color in COLORS:
            for key, count in CARD_COUNTS.iteritems():
                cards_to_add = [Card(color, key) for i in xrange(0, count)]
                self.deck.extend(cards_to_add)
        random.shuffle(self.deck)

        # Deal initial hands
        self.players = [Player(i) for i in xrange(0, NUM_PLAYERS)]
        for player in self.players:
            for i in xrange(0, HAND_SIZE):
                player.hand[i] = self.deck.pop()
            #print player.hand

    def get_playable_cards(self):
        playable_cards = []
        for color, card_list in self.table.iteritems():
            if len(card_list) == 0:
                playable_cards.append(Card(color, 1))
            elif len(card_list) != 5:
                top_card = card_list[-1]
                playable_cards.append(Card(color, top_card.number+1))
        return playable_cards

    def get_useless_cards(self):
        useless_cards = []
        # all cards that have already been played
        for color, card_list in self.table.iteritems():
            useless_cards += card_list

        # cards that can't be played because there are no remaining copies of one of its unplayed prereqs
        for color in COLORS:
            color_discarded = [card for card in self.graveyard if card.color == color]

            #for each rank, if the number discarded equals the total number, all higher cards are useless
            for rank in xrange(1, 6):
                color_rank_discarded = [card for card in color_discarded if card.number == rank]
                if len(color_rank_discarded) >= CARD_COUNTS[rank]:
                    for higher_rank in xrange(rank + 1, 6):
                        useless_cards.append(Card(color, higher_rank))
        return useless_cards

    def mark_turn_taken(self):
        if self.turn_taken:
            sys.exit("Tried to take an extra turn!")
        self.turn_taken = True

class Card(object):

    def __init__(self, color, number):
        self.color = color
        self.number = number

    def __repr__(self):
        return "%s %s" % (self.color, self.number)

    def __eq__(self, other_card):
        if self.color == other_card.color and self.number == other_card.number:
            return True


class Player:

    def __init__(self, number):
        self.hand = [None] * HAND_SIZE
        self.knowledge = [Card(None, None) for i in xrange(0, HAND_SIZE)]
        self.number = number

    def take_turn(self):
        next_player = game.players[(self.number + 1) % NUM_PLAYERS]
        my_playable_cards = self.get_playable_cards_for_player(self)
        next_player_playable_cards = self.get_playable_cards_for_player(next_player)

        # Plays card from hand if one is known to be playable
        if len(my_playable_cards) > 0:
            self.play_card(my_playable_cards[0])

        # If clues remain and next player has a playable card, gives clue about the card
        elif game.remaining_clues > 0 and len(next_player_playable_cards) > 0:
            clue_up = None
            for playable_card_index in next_player_playable_cards:
                card_knowledge = next_player.knowledge[playable_card_index]
                if card_knowledge.number is None:
                    clue_up = next_player.hand[playable_card_index].number
                elif card_knowledge.color is None:
                    clue_up = next_player.hand[playable_card_index].color
            if clue_up is not None:
                self.give_clue(clue_up, next_player)
                return
                
        # Plays known 1 or discards
        if not game.turn_taken:
            card_up = None
            for num, card in enumerate(self.knowledge):
                if card.number == 1:
                    card_up = num
            if card_up is not None:
                self.play_card(card_up)
            else:
                self.discard(0)

    def lose_card(self, index):
        lost = self.hand[index]
        self.hand[index] = game.deck.pop() if len(game.deck) > 0 else None
        self.knowledge[index] = Card(None, None)
        return lost

    def play_card(self, index):
        if self.hand[index] is None:
            sys.exit("Error: Tried to play a nonexistent card.")
        game.mark_turn_taken()

        played = self.lose_card(index)

        #print "Playing %r" % played

        if len(game.table[played.color]) == 0 and played.number == 1:
            game.table[played.color].append(played)
        elif len(game.table[played.color]) > 0 and game.table[played.color][-1].number == played.number - 1:
            game.table[played.color].append(played)
        else:
            game.graveyard.append(played)
            game.remaining_fuses -= 1


    def discard(self, index):
        game.mark_turn_taken()
        discarded = self.lose_card(index)

        #print "Discarding %r" % discarded

        game.remaining_clues = min(game.remaining_clues + 1, MAX_CLUES)
        game.graveyard.append(discarded)

    def give_clue(self, clue, receiving_player):
        game.mark_turn_taken()
        if receiving_player is self:
            sys.exit("Can't give yourself a clue")

        #print "Giving Player %d a clue about %ss" % (receiving_player.number, clue)
        receiving_player.receive_clue(clue)
        #print receiving_player.knowledge

    def receive_clue(self, clue):
        game.remaining_clues -= 1
        clue_type = 'number' if type(clue) == int else 'color'
        for index, card in enumerate(self.hand):
            if getattr(card, clue_type) == clue:
                #print "Card %d matches" % index
                setattr(self.knowledge[index], clue_type, clue)

    def get_playable_cards_for_player(self, player):
        playable_cards_for_player = []
        if player is self:
            # return playable cards from self knowledge
            for index, card in enumerate(self.knowledge):
                for playable_card in game.get_playable_cards():
                    if card == playable_card:
                        playable_cards_for_player.append(index)
        else:
            # return index of playable cards from player hand
            for index, card in enumerate(player.hand):
                for playable_card in game.get_playable_cards():
                    if card == playable_card:
                        playable_cards_for_player.append(index)
        #print "Player %d's %s card is playable!" % (player.number, playable_cards_for_player)
        return playable_cards_for_player

# Prepare to start playing games
random.seed(0)
total_score = 0

for i in xrange(0, NUMBER_OF_GAMES):
    # Start a game
    game = Game()

    # Take turns loop
    while not game.game_over:

        game.turn_taken = False
        current_player = game.players[game.whose_turn]

        #print "player %d's turn" % current_player.number
        current_player.take_turn()

        #pprint(game.table)
    
        #if game isn't over, prepare for next turn
        if game.remaining_fuses > 0 and game.last_turn < NUM_PLAYERS:
            game.whose_turn = (game.whose_turn + 1) % NUM_PLAYERS
            if len(game.deck) <= 0:
                game.game_over = True
                #sys.exit("Last turn under construction")
                game.last_turn += 1
        else:
            game.game_over = True

    color_scores = [len(color) for color in game.table.values()]
    final_score = sum(color_scores)
    print "Final Table:"
    pprint(game.table)
    print "Game Score: %d" % final_score
    print ""


    total_score += final_score

average_score = total_score / NUMBER_OF_GAMES
print "*****"
print "Average Score: %f" % average_score
