from multimeta import MultipleMeta # https://stackoverflow.com/a/49936625
import json
from copy import deepcopy

class Cards(metaclass=MultipleMeta):
    def __init__(self):
        # Load all the data from the json file
        with open('cards.json', 'r') as file:
            self.cards = json.load(file)

    def __repr__(self):
        return str([
            {'name': 'deck'},
            {'name': 'playing'},
            {'name': 'player'}
        ])

    def cards_get(self, id):
        return next(filter(lambda x: x['id'] == id, self.cards['cards']), {})
    
    def cards_deck_get(self):
        return [{"type": "main"}, {"type": "discarded"}, {"type": "removed"}]
    
    def cards_deck_get(self, deck: str): # Method overloading possible via MultipleMeta inheritance
        if deck in ['main', 'discarded', 'removed']:
            return deepcopy(self.cards['decks'][deck])
        return []
    
    def cards_deck_add(self, deck, id):
        if deck in ['main', 'discarded', 'removed'] and len([card for card in self.cards['decks'][deck] if card==id])==0:
            self.cards['decks'][deck].append(id)
            return True
        return False
    
    def cards_deck_remove(self, deck, id):
        if deck in ['main', 'discarded', 'removed'] and len([card for card in self.cards['decks'][deck] if card==id])==1:
            self.cards['decks'][deck].remove(id)
            return True
        return False
    
    def cards_playing_get(self):
        return self.cards['playing']
    
    def cards_playing_add(self, id):
        if id not in self.cards['playing']:
            self.cards['playing'].append(id)
            return True
        return False
    
    def cards_playing_remove(self, id):
        if id in self.cards['playing']:
            self.cards['playing'].remove(id)
            return True
        return False
    
    def cards_player_get(self, player):
        if player in list(self.cards['player'].keys()):
            return self.cards['player'][player]['hand']
        return []
    
    def cards_player_add(self, player, id):
        if player in list(self.cards['player'].keys()) and len([card for card in self.cards['player'][player]['hand'] if card==id])==0 and id in list(map(lambda x: x['id'], self.cards['cards'])):
            self.cards['player'][player]['hand'].append(id)
            return True
        return False
    
    def cards_player_remove(self, player, id):
        if player in list(self.cards['player'].keys()) and len([card for card in self.cards['player'][player]['hand'] if card==id])==1:
            self.cards['player'][player]['hand'].remove(id)
            return True
        return False
    
    def cards_player_header_get(self, player):
        if player in list(self.cards['player'].keys()):
            return self.cards['player'][player]['header']
        return {}
    
    def cards_player_header_unset(self, player):
        if player in list(self.cards['player'].keys()):
            id = self.cards['player'][player]['header']
            self.cards['player'][player]['header'] = None
            return id
        return False

    def cards_player_header_set(self, player, id):
        if player in list(self.cards['player'].keys()) and len([card for card in self.cards['player'][player]['hand'] if card==id])==1:
            self.cards['player'][player]['header'] = id
            return True
        return False
