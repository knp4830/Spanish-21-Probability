import random
from collections import Counter
from enum import Enum

class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    
    def value(self):
        """Return blackjack value of card"""
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Will be adjusted in hand evaluation
        else:
            return int(self.rank)
    
    def __repr__(self):
        return f"{self.rank}{self.suit.value}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

class Shoe:
    def __init__(self, num_decks=8):
        self.num_decks = num_decks
        self.cards = []
        self.reshuffle()
    
    def reshuffle(self):
        """Create new shoe with Spanish 21 decks (no 10s)"""
        self.cards = []
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'J', 'Q', 'K']
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))
        random.shuffle(self.cards)
    
    def deal(self):
        """Deal one card from shoe"""
        if len(self.cards) <= 50:
            self.reshuffle()
        return self.cards.pop()
    
    def cards_remaining(self):
        return len(self.cards)

class Hand:
    def __init__(self):
        self.cards = []
        self.bet = 0
        self.surrendered = False
        self.is_blackjack = False
    
    def add_card(self, card):
        self.cards.append(card)
    
    def value(self):
        """Calculate hand value, adjusting for aces"""
        total = sum(card.value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def is_hard(self):
        """Check if hand is hard (no usable ace)"""
        total = sum(card.value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        if aces == 0:
            return True
        
        # Check if using ace as 11 would bust
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return aces == 0
    
    def is_soft(self):
        """Check if hand is soft (has usable ace)"""
        return not self.is_hard() and 'A' in [card.rank for card in self.cards]
    
    def is_bust(self):
        return self.value() > 21
    
    def is_21(self):
        return self.value() == 21
    
    def card_count(self):
        return len(self.cards)

class MatchResult:
    def __init__(self):
        self.one_nonsuited = 0
        self.two_nonsuited = 0
        self.one_suited = 0
        self.one_suited_one_nonsuited = 0
        self.two_suited = 0

class Spanish21Simulator:
    def __init__(self):
        self.shoe = Shoe(8)
        self.stats = {
            'hands_played': 0,
            'hands_won': 0,
            'hands_lost': 0,
            'hands_pushed': 0,
            'hands_surrendered': 0,
            'top_matches': MatchResult(),
            'bottom_matches': MatchResult(),
            'top_bets_hit': 0,
            'bottom_bets_hit': 0,
            'total_top_bet_payout': 0,
            'total_bottom_bet_payout': 0,
            'total_top_bet_wagered': 0,
            'total_bottom_bet_wagered': 0,
            'total_regular_wagered': 0,
            'total_regular_payout': 0,
        }
    
    def evaluate_match(self, player_cards, dealer_card):
        """Evaluate matching between player cards and dealer card"""
        matches = {'suited': 0, 'nonsuited': 0}
        
        for card in player_cards:
            if card.rank == dealer_card.rank:
                if card.suit == dealer_card.suit:
                    matches['suited'] += 1
                else:
                    matches['nonsuited'] += 1
        
        return matches
    
    def calculate_match_payout(self, matches):
        """Calculate payout based on matching result"""
        suited = matches['suited']
        nonsuited = matches['nonsuited']
        
        if suited == 2:
            return 24  # 2 suited matches
        elif suited == 1 and nonsuited == 1:
            return 15  # 1 suited + 1 non-suited
        elif suited == 1:
            return 12  # 1 suited match
        elif nonsuited == 2:
            return 6   # 2 non-suited matches
        elif nonsuited == 1:
            return 3   # 1 non-suited match
        else:
            return 0   # No match
    
    def update_match_stats(self, matches, match_result):
        """Update match statistics"""
        suited = matches['suited']
        nonsuited = matches['nonsuited']
        
        if suited == 2:
            match_result.two_suited += 1
        elif suited == 1 and nonsuited == 1:
            match_result.one_suited_one_nonsuited += 1
        elif suited == 1:
            match_result.one_suited += 1
        elif nonsuited == 2:
            match_result.two_nonsuited += 1
        elif nonsuited == 1:
            match_result.one_nonsuited += 1
    
    def should_hit(self, player_hand, dealer_upcard, auto_surrender, has_top_match):
        """Spanish 21 basic strategy"""
        player_value = player_hand.value()
        dealer_value = dealer_upcard.value()
        is_soft = player_hand.is_soft()
        
        # Auto surrender logic - only if matched top card
        if auto_surrender and len(player_hand.cards) == 2 and has_top_match:
            if player_hand.is_hard() and 13 <= player_value <= 16:
                if dealer_upcard.rank in ['7', '8', '9', 'J', 'Q', 'K', 'A']:
                    return 'surrender'
        
        # Soft hands
        if is_soft:
            if player_value <= 17:
                return 'hit'
            elif player_value == 18:
                if dealer_value >= 9:
                    return 'hit'
                else:
                    return 'stand'
            else:
                return 'stand'
        
        # Hard hands
        if player_value <= 11:
            return 'hit'
        elif player_value == 12:
            if dealer_value in [4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif 13 <= player_value <= 16:
            if dealer_value <= 6:
                return 'stand'
            else:
                return 'hit'
        else:  # 17+
            return 'stand'
    
    def play_hand(self, hand, dealer_upcard, auto_surrender, has_top_match):
        """Play out a hand using basic strategy"""
        while True:
            action = self.should_hit(hand, dealer_upcard, auto_surrender, has_top_match)
            
            if action == 'surrender':
                hand.surrendered = True
                return
            elif action == 'stand':
                return
            elif action == 'hit':
                hand.add_card(self.shoe.deal())
                if hand.is_bust():
                    return
    
    def play_dealer_hand(self, dealer_hand):
        """Dealer hits on soft 17"""
        while dealer_hand.value() < 17 or (dealer_hand.value() == 17 and dealer_hand.is_soft()):
            dealer_hand.add_card(self.shoe.deal())
    
    def determine_winner(self, player_hand, dealer_hand):
        """Determine winner and return payout multiplier"""
        if player_hand.surrendered:
            self.stats['hands_surrendered'] += 1
            return 0.5  # Get half bet back
        
        if player_hand.is_bust():
            self.stats['hands_lost'] += 1
            return 0  # Lost
        
        player_value = player_hand.value()
        
        # Check for player blackjack (natural 21 with 2 cards)
        if len(player_hand.cards) == 2 and player_value == 21:
            self.stats['hands_won'] += 1
            return 2.5  # 3:2 payout
        
        # Check for 21 with 5 cards
        if player_value == 21 and len(player_hand.cards) == 5:
            self.stats['hands_won'] += 1
            return 2.5  # 3:2 payout
        
        # Check for 21 with 6 cards
        if player_value == 21 and len(player_hand.cards) == 6:
            self.stats['hands_won'] += 1
            return 3  # 2:1 payout
        
        # Regular 21 (3+ cards)
        if player_value == 21:
            self.stats['hands_won'] += 1
            return 2  # 1:1 payout
        
        # Dealer busts
        if dealer_hand.is_bust():
            self.stats['hands_won'] += 1
            return 2  # 1:1 payout
        
        dealer_value = dealer_hand.value()
        
        # Compare hands
        if player_value > dealer_value:
            self.stats['hands_won'] += 1
            return 2  # 1:1 payout
        elif player_value == dealer_value:
            self.stats['hands_pushed'] += 1
            return 1  # Push
        else:
            self.stats['hands_lost'] += 1
            return 0  # Lost
    
    def simulate_round(self, num_hands, regular_bet, top_bet, bottom_bet, auto_surrender):
        """Simulate one round with multiple hands"""
        player_hands = [Hand() for _ in range(num_hands)]
        dealer_hand = Hand()
        
        # Initial deal
        for hand in player_hands:
            hand.add_card(self.shoe.deal())
            hand.bet = regular_bet
        dealer_hand.add_card(self.shoe.deal())  # Dealer upcard
        
        for hand in player_hands:
            hand.add_card(self.shoe.deal())
        dealer_hand.add_card(self.shoe.deal())  # Dealer hole card
        
        # Check for dealer blackjack
        dealer_has_blackjack = (len(dealer_hand.cards) == 2 and dealer_hand.value() == 21)
        
        total_payout = 0
        
        # Evaluate side bets and store match info for each hand
        hand_has_top_match = []
        for hand in player_hands:
            # Top card match
            has_match = False
            if top_bet > 0:
                top_matches = self.evaluate_match(hand.cards, dealer_hand.cards[0])
                top_payout = self.calculate_match_payout(top_matches)
                if top_payout > 0:
                    has_match = True
                    self.stats['top_bets_hit'] += 1
                    total_payout += top_bet * top_payout
                    self.stats['total_top_bet_payout'] += top_bet * top_payout
                    self.update_match_stats(top_matches, self.stats['top_matches'])
                self.stats['total_top_bet_wagered'] += top_bet
            hand_has_top_match.append(has_match)
            
            # Bottom card match
            if bottom_bet > 0:
                bottom_matches = self.evaluate_match(hand.cards, dealer_hand.cards[1])
                bottom_payout = self.calculate_match_payout(bottom_matches)
                if bottom_payout > 0:
                    self.stats['bottom_bets_hit'] += 1
                    total_payout += bottom_bet * bottom_payout
                    self.stats['total_bottom_bet_payout'] += bottom_bet * bottom_payout
                    self.update_match_stats(bottom_matches, self.stats['bottom_matches'])
                self.stats['total_bottom_bet_wagered'] += bottom_bet
        
        # Play regular hands if dealer doesn't have blackjack
        if not dealer_has_blackjack:
            for i, hand in enumerate(player_hands):
                # Check for player blackjack
                if len(hand.cards) == 2 and hand.value() == 21:
                    hand.is_blackjack = True
                else:
                    self.play_hand(hand, dealer_hand.cards[0], auto_surrender, hand_has_top_match[i])
            
            # Dealer plays if at least one player didn't bust/surrender
            if any(not hand.is_bust() and not hand.surrendered for hand in player_hands):
                self.play_dealer_hand(dealer_hand)
        
        # Determine winners and payouts
        for hand in player_hands:
            self.stats['total_regular_wagered'] += regular_bet
            
            if dealer_has_blackjack:
                if hand.is_blackjack:
                    # Push on blackjack vs blackjack
                    self.stats['hands_pushed'] += 1
                    total_payout += regular_bet
                    self.stats['total_regular_payout'] += regular_bet
                else:
                    # Player loses to dealer blackjack
                    self.stats['hands_lost'] += 1
                    # No payout (already accounted for by not adding anything)
            else:
                multiplier = self.determine_winner(hand, dealer_hand)
                payout = regular_bet * multiplier
                total_payout += payout
                self.stats['total_regular_payout'] += payout
        
        self.stats['hands_played'] += num_hands
        return total_payout

def main():
    print("=" * 60)
    print("SPANISH 21 PROBABILITY CALCULATOR")
    print("Muckleshoot Casino Rules (8 Decks)")
    print("=" * 60)
    print()
    
    # Get user inputs
    try:
        bankroll = float(input("Starting bankroll ($): "))
        regular_bet = float(input("Regular bet amount (min $10): "))
        if regular_bet < 10:
            print("Regular bet must be at least $10. Setting to $10.")
            regular_bet = 10
        
        top_bet = float(input("Match dealer top card bet (min $2, 0 to skip): "))
        if top_bet > 0 and top_bet < 2:
            print("Side bet must be at least $2. Setting to $2.")
            top_bet = 2
        
        bottom_bet = float(input("Match dealer bottom card bet (min $2, 0 to skip): "))
        if bottom_bet > 0 and bottom_bet < 2:
            print("Side bet must be at least $2. Setting to $2.")
            bottom_bet = 2
        
        surrender_input = input("Surrender hard 13-16 vs 7-A when top card matched? (yes/no): ").lower()
        auto_surrender = surrender_input in ['yes', 'y']
        
        hands_per_round = int(input("How many hands at a time? "))
        total_hands = int(input("Total number of hands to play? "))
        
    except ValueError:
        print("Invalid input. Please enter valid numbers.")
        return
    
    print("\n" + "=" * 60)
    print("SIMULATION STARTING...")
    print("=" * 60)
    
    simulator = Spanish21Simulator()
    current_bankroll = bankroll
    rounds_played = 0
    total_rounds = total_hands // hands_per_round
    
    bet_per_round = (regular_bet + top_bet + bottom_bet) * hands_per_round
    
    for round_num in range(total_rounds):
        # Check if we have enough bankroll
        if current_bankroll < bet_per_round:
            print(f"\nInsufficient funds after {simulator.stats['hands_played']} hands!")
            print(f"Needed: ${bet_per_round:.2f}, Available: ${current_bankroll:.2f}")
            break
        
        # Deduct bets
        current_bankroll -= bet_per_round
        
        # Play round
        payout = simulator.simulate_round(hands_per_round, regular_bet, top_bet, bottom_bet, auto_surrender)
        current_bankroll += payout
        rounds_played += 1
    
    # Print results
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    print(f"\nStarting Bankroll: ${bankroll:.2f}")
    print(f"Final Bankroll: ${current_bankroll:.2f}")
    print(f"Net Profit/Loss: ${current_bankroll - bankroll:.2f}")
    print(f"\nHands Played: {simulator.stats['hands_played']}")
    print(f"Rounds Played: {rounds_played} / {total_rounds}")
    
    print("\n" + "-" * 60)
    print("HAND RESULTS")
    print("-" * 60)
    print(f"Hands Won: {simulator.stats['hands_won']}")
    print(f"Hands Lost: {simulator.stats['hands_lost']}")
    print(f"Hands Pushed: {simulator.stats['hands_pushed']}")
    print(f"Hands Surrendered: {simulator.stats['hands_surrendered']}")
    if simulator.stats['hands_played'] > 0:
        win_rate = (simulator.stats['hands_won'] / simulator.stats['hands_played']) * 100
        print(f"Win Rate: {win_rate:.2f}%")
    
    print("\n" + "-" * 60)
    print("REGULAR BET STATISTICS")
    print("-" * 60)
    print(f"Total Wagered: ${simulator.stats['total_regular_wagered']:.2f}")
    print(f"Total Returned: ${simulator.stats['total_regular_payout']:.2f}")
    regular_ev = simulator.stats['total_regular_payout'] - simulator.stats['total_regular_wagered']
    print(f"Net EV: ${regular_ev:.2f}")
    if simulator.stats['total_regular_wagered'] > 0:
        regular_roi = (regular_ev / simulator.stats['total_regular_wagered']) * 100
        print(f"ROI: {regular_roi:.2f}%")
    
    # Top card match statistics
    if simulator.stats['total_top_bet_wagered'] > 0:
        print("\n" + "-" * 60)
        print("MATCH DEALER TOP CARD STATISTICS")
        print("-" * 60)
        print(f"Total Side Bets Hit: {simulator.stats['top_bets_hit']}")
        top_stats = simulator.stats['top_matches']
        print(f"1 Non-suited Match: {top_stats.one_nonsuited}")
        print(f"2 Non-suited Matches: {top_stats.two_nonsuited}")
        print(f"1 Suited Match: {top_stats.one_suited}")
        print(f"1 Suited + 1 Non-suited: {top_stats.one_suited_one_nonsuited}")
        print(f"2 Suited Matches: {top_stats.two_suited}")
        print(f"\nTotal Wagered: ${simulator.stats['total_top_bet_wagered']:.2f}")
        print(f"Total Returned: ${simulator.stats['total_top_bet_payout']:.2f}")
        top_ev = simulator.stats['total_top_bet_payout'] - simulator.stats['total_top_bet_wagered']
        print(f"Net EV: ${top_ev:.2f}")
        top_roi = (top_ev / simulator.stats['total_top_bet_wagered']) * 100
        print(f"ROI: {top_roi:.2f}%")
    
    # Bottom card match statistics
    if simulator.stats['total_bottom_bet_wagered'] > 0:
        print("\n" + "-" * 60)
        print("MATCH DEALER BOTTOM CARD STATISTICS")
        print("-" * 60)
        print(f"Total Side Bets Hit: {simulator.stats['bottom_bets_hit']}")
        bottom_stats = simulator.stats['bottom_matches']
        print(f"1 Non-suited Match: {bottom_stats.one_nonsuited}")
        print(f"2 Non-suited Matches: {bottom_stats.two_nonsuited}")
        print(f"1 Suited Match: {bottom_stats.one_suited}")
        print(f"1 Suited + 1 Non-suited: {bottom_stats.one_suited_one_nonsuited}")
        print(f"2 Suited Matches: {bottom_stats.two_suited}")
        print(f"\nTotal Wagered: ${simulator.stats['total_bottom_bet_wagered']:.2f}")
        print(f"Total Returned: ${simulator.stats['total_bottom_bet_payout']:.2f}")
        bottom_ev = simulator.stats['total_bottom_bet_payout'] - simulator.stats['total_bottom_bet_wagered']
        print(f"Net EV: ${bottom_ev:.2f}")
        bottom_roi = (bottom_ev / simulator.stats['total_bottom_bet_wagered']) * 100
        print(f"ROI: {bottom_roi:.2f}%")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()