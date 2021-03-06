from __future__ import division
from pprint import pprint
import random
import sys

NUM_PLAYERS = 3
HAND_SIZE = 5 if NUM_PLAYERS < 4 else 4
COLORS = ['pink', 'blue', 'white', 'yellow', 'green']
CARD_COUNTS = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}
MAX_CLUES = 8
NUMBER_OF_GAMES = 50
NAMES = {
    'infosec': ['Alice', 'Bob', 'Carol', 'Dave', 'Eve'],
    'megaman': ['Air Man', 'Bubble Man', 'Crash Man', 'Dust Man', 'Elec Man'],
    'pokemon': ['Abra', 'Bulbasaur', 'Charmander', 'Diglett', 'Eevee'],
    'worm':    ['Alexandria', 'Behemoth', 'Coil', 'Dragon', 'Eidolon'],
    'numbers': ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5']
}['megaman']

final_scores = []
discarded_reserves = 0
burned_fuses = 0
game_print_level = 4
#TODO: in game prints for all actions and thoughts gauged by number for level of importance

#game_print_level 0: Best score, worst score, and averages out of # of games played
#game_print_level 1: Final table, score, and game # of each game
#game_print_level 2: Each burned fuses and discarded reserve
#game_print_level 3: Player turn, action (play, discard, clue), game table, hand, clues, fuses, and deck remaining
#game_print_level 4: Player knowledge and hand age each turn
#game_print_level 5: TODO: Inferences
#game_print_level 6: TODO: Reasoning (thoughts leading to actions, knowledge, and inferences)

def print_at_level(priority_level, message):
    if priority_level <= game_print_level:
        if type(message) == str:
            print message
        else:
            pprint(message)

# Current 50 Game Scores:
# Best: 23
# Worst: 17
# Average: 19.820000


class Game:
    
    def __init__(self):
        self.game_over = False
        self.remaining_fuses = 3
        self.remaining_clues = 8
        self.whose_turn = 0
        self.last_turn = 0
        self.unseen_cards = self.build_deck()
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
            print_at_level(3, "%r's hand: %r" % (player, player.hand))

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
        self.inferred_playables = [None] * HAND_SIZE # [Blue 2, Green 2]

    def __repr__(self):
        return NAMES[self.number]

    def take_turn(self):

        # Play a card from my hand if one is known to be playable
        my_playable_cards = self.get_known_playable_cards(self)
        if len(my_playable_cards) > 0:
            self.play_card(my_playable_cards[0])
            return

        # Play inferred playables
        for index, card_list in enumerate(self.inferred_playables):
            if card_list:
                self.play_card(index)
                return

        # If it's the last turn, try and play your playable cards.
        if game.last_turn > 0 and game.remaining_fuses > 1:
            playable_probabilities = self.get_known_playable_cards(self, True)
            best_chance = max(playable_probabilities)
            if best_chance > 0:
                self.play_card(playable_probabilities.index(best_chance))
                return

        # If we can give a clue, do so to the first player that needs help
        if game.remaining_clues > 0:
            next_players = self.get_next_players()

            for player_index, player in enumerate(next_players):
                # Does this guy have playable cards and not know it?
                if len(self.get_known_playable_cards(player)) == 0 and len(self.get_playable_cards_for_player(player)) > 0:
                    possible_clues = []

                    # Tell him about his playable card(s)!
                    for playable_card_index in self.get_playable_cards_for_player(player):
                        card_knowledge = player.knowledge[playable_card_index]
                        if card_knowledge.number is None:
                            possible_clues.append(player.hand[playable_card_index].number)
                        elif card_knowledge.color is None:
                            possible_clues.append(player.hand[playable_card_index].color)

                    if len(possible_clues) > 0:
                        if 5 in possible_clues:
                            self.give_clue(5, player)
                        else:
                            self.give_clue(possible_clues[-1], player)  # for some reason (probably random), giving the last clue is better
                        return

                # If player is about to discard a reserved card, stop him
                reserved_cards = game.get_reserved_cards()
                next_discard = player.hand[self.get_best_discard(player)]
                if next_discard in reserved_cards and game.remaining_clues < NUM_PLAYERS:

                    # First, see if we can safely communicate where some reserved cards are
                    if self.count_clue_matches(next_discard.number, player) > 1:
                        self.give_clue(next_discard.number, player)
                        return
                    if self.count_clue_matches(next_discard.color, player) > 1:
                        self.give_clue(next_discard.color, player)
                        return

                    # If not, try to point out some safe discards
                    high_match = 0
                    clue_up = None
                    for useless_card_index in self.get_useless_cards_for_player(player):
                        # Check whether we can safely communicate where some useless cards are
                        useless_card = player.hand[useless_card_index]
                        useless_of_number = [card for card in game.get_useless_cards() if card.number == useless_card.number]
                        if len(useless_of_number) == len(COLORS):
                            clue_matches = self.count_clue_matches(useless_card.number, player)
                            if clue_matches > high_match:
                                clue_up = useless_card.number
                                high_match = clue_matches
                        if len(game.table[useless_card.color]) == 5:
                            clue_matches = self.count_clue_matches(useless_card.color, player)
                            if clue_matches > high_match:
                                clue_up = useless_card.color
                                high_match = clue_matches
                    if clue_up is not None:
                        self.give_clue(clue_up, player)
                        return
                
        if not game.turn_taken:
            self.discard(self.get_best_discard(self))

    def count_clue_matches(self, clue, player):
        clue_type = 'number' if type(clue) == int else 'color'
        matches = [card for card in player.hand if card and getattr(card, clue_type) == clue]
        return len(matches)

    def get_best_discard(self, player):
        player_useless_cards = self.get_known_useless_cards(player)
        player_reserved_cards = self.get_known_reserved_cards(player)

        if len(player_useless_cards) > 0:
            return player_useless_cards[0]
        else:
            discardables = [index for index, card in enumerate(player.knowledge) if card.color is None and card.number is None]
            if len(discardables) < 1:
                discardables = [index for index, card in enumerate(player.knowledge) if card.color is None or card.number is None]
            if len(discardables) < 1:
                discardables = [index for index, card in enumerate(player.knowledge) if index not in player_reserved_cards]

            for hand_index in player.hand_age:
                if hand_index in discardables:
                    return hand_index
        return player.hand_age[0]

    def lose_card(self, index):
        lost = self.hand[index]
        game.unseen_cards.remove(lost)
        self.hand_age.remove(index)
        drawn_card = None

        self.remove_from_public_knowledge(lost)
        self.remove_from_private_knowledge(lost)

        if len(game.deck) > 0:
            drawn_card = game.deck.pop()
            self.hand[index] = drawn_card
            self.hand_age.append(index)
        else:
            self.hand[index] = None

        self.knowledge[index] = Card(None, None)
        self.public_knowledge[index] = [card for card in game.unseen_cards]
        self.private_knowledge[index] = [card for card in game.unseen_cards]

        other_players = self.get_next_players()
        # private knowledge about the drawn card accounts for other players' hands
        for player in other_players:
            for card in player.hand:
                if card is not None:
                    self.private_knowledge[index].remove(card)

        self.inferred_playables[index] = None

        # other players see the card you just grabbed and update their private knowledge
        if drawn_card:
            for player in other_players:
                player.remove_from_private_knowledge(drawn_card)
        return lost

    def play_card(self, index):
        if self.hand[index] is None:
            sys.exit("Error: Tried to play a nonexistent card.")
        game.mark_turn_taken()

        played = self.lose_card(index)

        print_at_level(3, "%r plays a %r" % (current_player, played))
        if self.hand[index] is not None:
            print_at_level(3, "%r draws a %r" % (current_player, self.hand[index]))
        else:
            print_at_level(3, "The deck is empty")

        if played in game.get_playable_cards():
            game.table[played.color].append(played)
            if played.number == 5:
                game.remaining_clues = min(game.remaining_clues + 1, MAX_CLUES)

            #Removes inference that has a card that matches played card
            for player in game.players:
                for index, card_list in enumerate(player.inferred_playables):
                    if card_list is not None and played in card_list:
                        player.inferred_playables[index] = None
                        break

        else:
            game.graveyard.append(played)
            game.remaining_fuses -= 1
            print_at_level(2, "Burned a fuse!!!")
            global burned_fuses
            burned_fuses += 1

    def discard(self, index):
        game.mark_turn_taken()
        discarded = self.lose_card(index)

        print_at_level(3, "%r discards a %r" % (current_player, discarded))
        if discarded in game.get_reserved_cards():
            print_at_level(2, "Discarded an irreplacable card!!!")
            global discarded_reserves
            discarded_reserves += 1
            if self.hand[index] is not None:
                print_at_level(3, "%r draws a %r" % (current_player, self.hand[index]))
            else:
                print_at_level(3, "The deck is empty")

        game.remaining_clues = min(game.remaining_clues + 1, MAX_CLUES)
        game.graveyard.append(discarded)

    def give_clue(self, clue, receiving_player):
        game.mark_turn_taken()
        if receiving_player is self:
            sys.exit("Error: Can't give yourself a clue")

        receiving_player.receive_clue(clue)

        print_at_level(3, "%r gives %r a clue about %ss" % (current_player, receiving_player, clue))

    def receive_clue(self, clue):
        game.remaining_clues -= 1
        clue_type = 'number' if type(clue) == int else 'color'
        matches = []
        for index, card in enumerate(self.hand):
            if card is not None and getattr(card, clue_type) == clue:
                setattr(self.knowledge[index], clue_type, clue)
                matches.append(index)

        if len(matches) == 0:
            sys.exit("Error: It's illegal to give a clue that the receiving player has zero of something")

        for i in xrange(0, HAND_SIZE):
            if i in matches:
                self.public_knowledge[i] = [card for card in self.public_knowledge[i] if getattr(card, clue_type) == clue]
                self.private_knowledge[i] = [card for card in self.private_knowledge[i] if getattr(card, clue_type) == clue]
            else:
                self.public_knowledge[i] = [card for card in self.public_knowledge[i] if getattr(card, clue_type) != clue]
                self.private_knowledge[i] = [card for card in self.private_knowledge[i] if getattr(card, clue_type) != clue]

        # When a clue only matches one card, a list of playable cards from the
        # private knowledge index of that card is added to that index of inferred playables

        # TODO: be more aggressive about inferring playability. If clue matches multiple cards, maybe assume they're all playable
        # ALSO TODO: might need to update the clue-giving strategy to match this more optimistic interpretation
        if len(matches) == 1:
            match_index = matches[0]
            inferred_playables = []
            playable_cards = game.get_playable_cards()
            for possible_card in self.private_knowledge[match_index]:
                if possible_card in playable_cards:
                    inferred_playables.append(possible_card)

            if len(inferred_playables) > 0:
                self.inferred_playables[match_index] = inferred_playables

    def get_cards_in_list(self, player, card_list):
        if player is self:
            sys.exit("Can't call get_cards_in_list on self. Use get_known_cards_in_list instead.")

        player_card_matches = []
        for index, card in enumerate(player.hand):
            if card is not None and card in card_list:
                player_card_matches.append(index)
        return player_card_matches

    def get_known_cards_in_list(self, player, card_list, get_probabilities=False):
        player_card_matches = []
        knowledge = player.private_knowledge if player is self else player.public_knowledge
        for index, possibilities in enumerate(knowledge):
            hits = [True for possible_card in possibilities if possible_card in card_list]
            if get_probabilities:
                player_card_matches.append(len(hits) / len(possibilities))
            elif len(hits) == len(possibilities) and player.hand[index] is not None:
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

    def get_known_playable_cards(self, player, get_probabilites=False):
        playable_cards = game.get_playable_cards()
        return self.get_known_cards_in_list(player, playable_cards, get_probabilites)

    def get_known_useless_cards(self, player, get_probabilites=False):
        useless_cards = game.get_useless_cards()
        return self.get_known_cards_in_list(player, useless_cards, get_probabilites)

    def get_known_reserved_cards(self, player, get_probabilites=False):
        reserved_cards = game.get_reserved_cards()
        return self.get_known_cards_in_list(player, reserved_cards, get_probabilites)

    # returns players in order of turn after next player, up to the current player
    def get_next_players(self):
        next_players = []
        number = (self.number + 1) % NUM_PLAYERS
        for _ in xrange(0, NUM_PLAYERS - 1):
            next_players.append(game.players[number])
            number = (number + 1) % NUM_PLAYERS
        return next_players

    def init_knowledge(self):
        self.public_knowledge = [game.build_deck() for _ in xrange(0, HAND_SIZE)]

        private_deck = game.build_deck()
        for player in self.get_next_players():
            for card in player.hand:
                private_deck.remove(card)

        self.private_knowledge = [list(private_deck) for _ in xrange(0, HAND_SIZE)]

    def remove_from_private_knowledge(self, card):
        for card_list in self.private_knowledge:
            if card in card_list:
                card_list.remove(card)

    def remove_from_public_knowledge(self, card):
        for card_list in self.public_knowledge:
            if card in card_list:
                card_list.remove(card)

# Prepare to start playing games
random.seed(0)

for game_number in xrange(0, NUMBER_OF_GAMES):
    #TODO: study worst game (number 31) for strategy ideas
    #if game_number == 31:
        #game_print_level = 9
    #else:
        #game_print_level = 0

    # Start a game
    game = Game()
    turn = 1

    for player in game.players:
        player.init_knowledge()

    # Take turns loop
    while not game.game_over:

        print_at_level(3, "*****")
        print_at_level(3, "Starting turn %d of game %d" % (turn, game_number))

        game.turn_taken = False
        current_player = game.players[game.whose_turn]

        print_at_level(3, "%r's turn" % current_player)
            
        current_player.take_turn()
        if not game.turn_taken:
            sys.exit("Player failed to take an action!")

        print_at_level(3, "Game Table:")
        print_at_level(2, game.table)
        for player in game.players:
            print_at_level(3, "%r's hand: %s" % (player, player.hand))
            print_at_level(4, "%r knows: %s" % (player, player.knowledge))
            print_at_level(4, "%r's hand age: %s" % (player, player.hand_age))
        print_at_level(3, "Clues remaining: %d" % game.remaining_clues)
        print_at_level(3, "Fuses remaining: %d" % game.remaining_fuses)
        #def deck_remaining:
           # x=
          #  for cards in game.deck:
          #      placeholder text
        print_at_level(3, "Deck remaining: %r" % len(game.deck))

        #if game isn't over, prepare for next turn
        if game.remaining_fuses > 0 and game.last_turn < NUM_PLAYERS:
            turn += 1
            game.whose_turn = (game.whose_turn + 1) % NUM_PLAYERS
            if len(game.deck) <= 0:
                game.last_turn += 1
        else:
            game.game_over = True

        # Validates every player's public and private knowledge.
        for player in game.players:
            for index, card in enumerate(player.hand):
                if card:
                    if card not in player.public_knowledge[index] or card not in player.private_knowledge[index]:
                        sys.exit("Error: %r believes a card in his hand (%r at %d) is impossible" % (player, card, index))

    color_scores = [len(card_list) for card_list in game.table.values()]
    final_score = sum(color_scores)
    print_at_level(1, "*****")
    print_at_level(1, "Game %i's Final Table:" % game_number)
    print_at_level(1, game.table)
    print_at_level(1, "Game Score: %d" % final_score)
    print_at_level(1, "")

    final_scores.append(final_score)

best_score = max(score for score in final_scores)
worst_score = min(score for score in final_scores)
average_score = sum(final_scores) / NUMBER_OF_GAMES
print "*****"
print "Out of %i Games:" % NUMBER_OF_GAMES
print "*****"
print "Best Score: %i" % best_score
print "Worst Score: %i" % worst_score
print "Average Score: %f" % average_score
print "Average number of reserved cards discarded: %f" % (discarded_reserves / NUMBER_OF_GAMES)
print "Average number of fuses burned: %f" % (burned_fuses / NUMBER_OF_GAMES)
