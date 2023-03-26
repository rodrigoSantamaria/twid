from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625
from copy import deepcopy
import json


class Board(metaclass=MultipleMeta):
    def __init__(self):
        # Load all the data from the json file
        with open('board.json', 'r') as file:
            self.board = json.load(file)

    def __repr__(self):
        return str([
            {'name': 'round'},
            {'name': 'score'},
            {'name': 'map'},
            {'name': 'nwo'}
        ])

    # Round methods
    def round_get(self):
        return self.board['round']

    def round_add(self):
        if self.board['round'] < 8:
            self.board['round'] += 1
            return True
        return False

    def round_reset(self):
        self.board['round'] = 1

    # Score methods
    def score_get(self):
        return self.board['score']

    def score_player_get(self, player):
        # If the player exists
        if player in self.board['players']:
            # https://book.pythontips.com/en/latest/map_filter.html
            # Filter self.board['score'] with filter for the specified player
            # Then map the result so it looks like {'score': $score}

            # https://stackoverflow.com/questions/29563153/python-filter-function-single-result
            # And finally get the element of the iterator
            return next(map(lambda x: x['score'], filter(lambda x: x['name'] == player, self.board['score'])), {})
        return {}

    def score_player_put(self, player, score):
        # If the player exists and 0 <= score <= 100
        if player in self.board['players'] and score >= 0 and score <= 100:
            for index, item in enumerate(self.board['score']):
                if item['name'] == player:
                    self.board['score'][index]['score'] = score
                    return True

        return False

    # Map methods
    def map_get(self):
        return self.board['regions']

    def map_region_get(self, region):
        return [{'country': country['name']} for country in self.board['countries'] if country['region'] == region]
    
    def map_region_put(self, region, countries):
        # If the regions and all of the countries exist
        if region in self.board['regions'] and set([country['country'] for country in countries]).issubset([country['name'] for country in self.board['countries']]): # https://stackoverflow.com/questions/3931541/how-to-check-if-all-of-the-following-items-are-in-a-list
            for index, item in enumerate(self.board['countries']):
                
                # Remove all the countries of the specified region
                if item['region'] == region:
                    self.board['countries'][index]['region'] = ''
            
                # Add all the specified new countries of the specified region
                if item['name'] in [country['country'] for country in countries]:
                    self.board['countries'][index]['region'] = region
            return True

        return False
    
    def map_region_country_get(self, region, country):
        return next(({'stability': item['stability'], 'isConflictive': item['isConflictive'], 'isOilProducer': item['isOilProducer'], 'influence': item['influence'], 'adjacent': item['adjacent']} for item in self.board['countries'] if item['region'] == region and item['name'] == country), {}) # https://stackoverflow.com/questions/58380706/python-list-comprehension-filter-single-element-in-the-list
    
    def map_country_get(self, country):
        return next(({'stability': item['stability'], 'isConflictive': item['isConflictive'], 'isOilProducer': item['isOilProducer'], 'influence': item['influence'], 'adjacent': item['adjacent']} for item in self.board['countries'] if item['name'] == country), {}) # https://stackoverflow.com/questions/58380706/python-list-comprehension-filter-single-element-in-the-list
    
    def map_country_put(self, country, newCountry):
        if set([country]).issubset([country['name'] for country in self.board['countries']]):
            for index, item in enumerate(self.board['countries']):
                
                if item['name'] == country:
                    # Check if all the values are valid
                    wrongValues = False
                    for indexPlayer in newCountry['influence']:
                        if newCountry['influence'][indexPlayer]['influence'] not in range(0, 100+1):
                            wrongValues = True
                            break
                        
                        # Check if all the values in the extra field are valid
                        for indexPlayerExtra in newCountry['influence'][indexPlayer]['extra']:
                            if newCountry['influence'][indexPlayer]['extra'][indexPlayerExtra] not in range(0, 100+1):
                                wrongValues = True
                                break

                    # If the stability and the influence have a valid value
                    if not wrongValues and newCountry['stability'] in range(0, 5+1):
                        self.board['countries'][index].update(newCountry) # https://stackoverflow.com/questions/405489/python-update-object-from-dictionary
                        return True

        return False
    
    def nwo_get(self):
        return list(self.board['nwo'].keys())
    
    def nwo_track_get(self, track):
        return list(self.board['nwo'][track].keys())
    
    def nwo_track_slot_get(self, track, slot):
        return deepcopy(self.board['nwo'][track][slot])
    
    def nwo_track_slot_put(self, track, slot, newSlot):
        # If the track and the slot exist
        if track in list(self.board['nwo'].keys()) and slot in list(self.board['nwo'][track].keys()):
            # Create an array of valid values
            validValues = self.board['players']
            validValues.append('')
            
            # Delete the description, that cannot be updated (for now)
            newSlot.pop('description', None)
            
            # If the new slot has valid values
            if newSlot['veto'] in validValues and newSlot['ahead'] in validValues and newSlot['supremacy'] in validValues:
                self.board['nwo'][track][slot].update(newSlot)
                return True
        
        return False
