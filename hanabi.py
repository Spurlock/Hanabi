from __future__ import division
from pprint import pprint
import random
import sys

NUM_PLAYERS = 3
HAND_SIZE = 5 # TODO: Compute HAND_SIZE from NUM_PLAYERS, for easier testing of different size games
COLORS = ['pink', 'blue', 'white', 'yellow', 'green']
CARD_COUNTS = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}
MAX_CLUES = 8
NUMBER_OF_GAMES = 50
# Current 50 Game Average Score: 16.16000


class Game:
    
    def __init__(self):
        self.game_over = False
        self.remaining_fuses = 3
        self.remaining_clues = 8
        self.whose_turn = 0
        self.last_turn = 0
        self.graveyard = []
        self.turn_taken = False
        self.table = {color: [] for color in COLORS}

        self.deck = self.build_deck()
        random.shuffle(self.deck)

        # Deal initial hands
        self.players = [Player(i) for i in xrange(0, NUM_PLAYERS)]
        for player in self.players:
            for i in xrange(0, HAND_SIZE):
                player.hand[i] = self.deck.pop()
                player.hand_age[i] = i
            #print player.hand

    def build_deck(self):
        deck = []
        for color in COLORS:
            for key, count in CARD_COUNTS.iteritems():
                cards_to_add = [Card(color, key) for i in xrange(0, count)]
                deck.extend(cards_to_add)
        return deck

    def get_playable_cards(self):
        playable_cards = []
        for color, card_list in self.table.iteritems():
            if len(card_list) < 5:
                playable_cards.append(Card(color, len(card_list) + 1))
        return playable_cards

    def get_useless_cards(self):
        useless_cards = []
        # all cards that have already been played
        for color, card_list in self.table.iteritems():
            useless_cards += card_list

        # cards that can't be played because there are no remaining copies of one of its unplayed prereqs
        for color in COLORS:
            color_discarded = [card for card in self.graveyard if card.color == color]

            # for each rank, if the number discarded equals the total number, all higher cards are useless
            for rank in xrange(1, 6):
                color_rank_discarded = [card for card in color_discarded if card.number == rank]
                if len(color_rank_discarded) >= CARD_COUNTS[rank]:
                    for higher_rank in xrange(rank + 1, 6):
                        useless_cards.append(Card(color, higher_rank))
        return useless_cards

    # TODO: Rather than recompute this every time, just add an unseen_cards property to the game,
    # and update it every time a card is played or discarded
    def get_unseen_cards(self):
        deck = self.build_deck()
        for card in self.graveyard:
            deck.remove(card)
        for color, card_stack in self.table.iteritems():
            for card in card_stack:
                deck.remove(card)
        return deck

    # Returns any card that isn't useless and only has one left of its type
    def get_reserved_cards(self):
        reserved_cards = []
        card_types = []
        useless_cards = self.get_useless_cards()
        for color in COLORS:
            for key in CARD_COUNTS:
                card_types.append(Card(color, key))

        for card in card_types:
            if card not in useless_cards:
                if self.graveyard.count(card) == CARD_COUNTS[card.number] - 1:
                    reserved_cards.append(card) 
        return reserved_cards

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
        return False


class Player:

    def __init__(self, number):
        self.hand = [None] * HAND_SIZE
        self.hand_age = [None] * HAND_SIZE
        self.knowledge = [Card(None, None) for _ in xrange(0, HAND_SIZE)]
        self.private_knowledge = []  # What I know
        self.public_knowledge = []  # What everyone knows I know
        self.number = number

    def take_turn(self):

        # Play a card from my hand if one is known to be playable
        my_playable_cards = self.get_known_playable_cards(self)
        if len(my_playable_cards) > 0:
            self.play_card(my_playable_cards[0])
            return

        # If clues remain and next player has a playable card, gives clue about the card
        # TODO: Use get_known_playable_cards to better check whether the player actually needs clues
        # TODO: If next player doesn't need a clue, consider the player after that
        next_player = game.players[(self.number + 1) % NUM_PLAYERS]
        next_player_playable_cards = self.get_playable_cards_for_player(next_player)

        if game.remaining_clues > 0 and len(next_player_playable_cards) > 0:
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

        #useless_cards = game.get_useless_cards()
        my_useless_cards = self.get_known_useless_cards(self)
        #reserved_cards = game.get_reserved_cards()
        my_reserved_cards = self.get_known_reserved_cards(self)
                
        if not game.turn_taken:
            if len(my_useless_cards) > 0:
                self.discard(my_useless_cards[0])
            else:
                discardables = [index for index, card in enumerate(self.knowledge) if card.color is None and card.number is None]
                if len(discardables) < 1:
                    discardables = [index for index, card in enumerate(self.knowledge) if card.color is None or card.number is None]
                if len(discardables) < 1:
                    discardables = [index for index, card in enumerate(self.knowledge) if index not in my_reserved_cards]

                for age in self.hand_age:
                    if age in discardables:
                        self.discard(age)
                        return

        if not game.turn_taken:
            print "*** WARNING! Using stupid discard! ***"
            self.discard(0)

    def lose_card(self, index):
        lost = self.hand[index]
        self.hand_age.remove(index)
        drawn_card = None

        if len(game.deck) > 0:
            drawn_card = game.deck.pop()
            self.hand[index] = drawn_card
            self.hand_age.append(index)
        else:
            self.hand[index] = None

        self.knowledge[index] = Card(None, None)
        self.public_knowledge[index] = game.get_unseen_cards()
        self.private_knowledge[index] = game.get_unseen_cards()

        # other players see the card you just grabbed and update their private knowledge
        if drawn_card:
            for player in game.players:
                if player is not self:
                    player.remove_from_private_knowledge(drawn_card)
        return lost

    def play_card(self, index):
        if self.hand[index] is None:
            sys.exit("Error: Tried to play a nonexistent card.")
        game.mark_turn_taken()

        played = self.lose_card(index)

        #print "Playing %r" % played

        if played in game.get_playable_cards():
            game.table[played.color].append(played)
            if played.number == 5:
                game.remaining_clues += 1
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
            sys.exit("Error: Can't give yourself a clue")

        #print "Giving Player %d a clue about %ss" % (receiving_player.number, clue)
        receiving_player.receive_clue(clue)
        #print receiving_player.knowledge

    def receive_clue(self, clue):
        game.remaining_clues -= 1
        clue_type = 'number' if type(clue) == int else 'color'
        matches = []
        # TODO: It's illegal to give a clue that the receiving player has zero of something, so check for that
        for index, card in enumerate(self.hand):
            if card is not None and getattr(card, clue_type) == clue:
                setattr(self.knowledge[index], clue_type, clue)
                matches.append(index)

        for i in xrange(0, HAND_SIZE):
            if i in matches:
                self.public_knowledge[i] = [card for card in self.public_knowledge[i] if getattr(card, clue_type) == clue]
                self.private_knowledge[i] = [card for card in self.private_knowledge[i] if getattr(card, clue_type) == clue]
            else:
                self.public_knowledge[i] = [card for card in self.public_knowledge[i] if getattr(card, clue_type) != clue]
                self.private_knowledge[i] = [card for card in self.private_knowledge[i] if getattr(card, clue_type) != clue]

    def get_cards_in_list(self, player, card_list):
        if player is self:
            sys.exit("Can't call get_cards_in_list on self. Use get_known_cards_in_list instead.")

        player_card_matches = []
        for index, card in enumerate(player.hand):
            if card is not None and card in card_list:
                player_card_matches.append(index)
        return player_card_matches

    def get_known_cards_in_list(self, player, card_list):
        player_card_matches = []
        knowledge = player.private_knowledge if player is self else player.public_knowledge
        for index, possibilities in enumerate(knowledge):
                hits = [True for possible_card in possibilities if possible_card in card_list]
                if len(hits) == len(possibilities):
                    player_card_matches.append(index)
        return player_card_matches

    def get_playable_cards_for_player(self, player):
        playable_cards = game.get_playable_cards()
        return self.get_cards_in_list(player, playable_cards)

    def get_useless_cards_for_player(self, player):
        useless_cards = game.get_useless_cards()
        return self.get_cards_in_list(player, useless_cards)

    def get_reserved_cards_for_player(self, player):
        reserved_cards = game.get_reserved_cards()
        return self.get_cards_in_list(player, reserved_cards)

    def get_known_playable_cards(self, player):
        playable_cards = game.get_playable_cards()
        return self.get_known_cards_in_list(player, playable_cards)

    def get_known_useless_cards(self, player):
        useless_cards = game.get_useless_cards()
        return self.get_known_cards_in_list(player, useless_cards)

    def get_known_reserved_cards(self, player):
        reserved_cards = game.get_reserved_cards()
        return self.get_known_cards_in_list(player, reserved_cards)

    def init_knowledge(self):
        self.public_knowledge = [game.build_deck()] * HAND_SIZE

        private_deck = game.build_deck()
        other_players = [player for player in game.players if player is not self]
        for player in other_players:
            for card in player.hand:
                private_deck.remove(card)

        self.private_knowledge = [list(private_deck) for _ in xrange(0, HAND_SIZE)]

    def remove_from_private_knowledge(self, card):
        for card_list in self.private_knowledge:
            if card in card_list:
                card_list.remove(card)

# Prepare to start playing games
random.seed(0)
total_score = 0

for i in xrange(0, NUMBER_OF_GAMES):
    # Start a game
    game = Game()

    # TODO: Move init_knowledge stuff into game's constructor
    for player in game.players:
        player.init_knowledge()

    # Take turns loop
    while not game.game_over:

        game.turn_taken = False
        current_player = game.players[game.whose_turn]

        #print "player %d's turn" % current_player.number
        current_player.take_turn()
        if not game.turn_taken:
            sys.exit("Player failed to take an action!")

        #pprint(game.table)

        #if game isn't over, prepare for next turn
        if game.remaining_fuses > 0 and game.last_turn < NUM_PLAYERS:
            game.whose_turn = (game.whose_turn + 1) % NUM_PLAYERS
            if len(game.deck) <= 0:
                game.last_turn += 1
        else:
            game.game_over = True

    color_scores = [len(card_list) for card_list in game.table.values()]
    final_score = sum(color_scores)
    print "Final Table:"
    pprint(game.table)
    print "Game Score: %d" % final_score
    print ""

    total_score += final_score

# TODO: Also print best and worst game scores
average_score = total_score / NUMBER_OF_GAMES
print "*****"
print "Average Score: %f" % average_score
