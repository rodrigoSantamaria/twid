import logging
import config
import requests
import random
import utils #custom package to simplify some common operations
from multimeta import MultipleMeta  # https://stackoverflow.com/a/49936625
import json


# Define the logger
logger = logging.getLogger('control_logger')


class Game(metaclass=MultipleMeta):
    #Private functions
    def __init__(self):
        response = requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game')
        self.id = response.json()['id']
        self.players = {'US': None, 'EU': None, 'Russia': None, 'China': None}
        self.playingOrder = [] # Will store the order in which the players have to play in the current round (defined after the last player plays his header card)
        self.playingOrderCurrent = []
        self.numSubRounds=0
        self.isStarted = False
        self.isHeaderPhase = False
        self.destabilization = None
        self.isFinished = False
        self.UEmembers=[ 'United Kingdom', 'Benelux', 'Denmark', 'Germany', 'France', 'Spain-Portugal', 'Italy', 'Greece']
        self.superpowers=["US", "Russia", "China"]
        self.factions={"US": "W", "EU": "W", "Russia":"E", "China":"E"}
        self.ifactions={"W":["EU","US"], "E":["Russia", "China"]}
        self.g20={}
        
  
    def __repr__(self):
        return self.id
    
    def __del__(self):
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}')

    #
    # Getters
    def get_players(self):
        return self.players
    
    def get_playingOrder(self):
        return self.playingOrder
    
    def get_playingOrderCurrent(self):
        return self.playingOrderCurrent
    
    def get_isStarted(self):
        return self.isStarted
    
    def get_isHeaderPhase(self):
        return self.isHeaderPhase

    #def get_isPostHeaderPhase(self):
    #    return self.isPostHeaderPhase

    def get_destabilization(self):
        return self.destabilization

    def get_isFinished(self):
        return self.isFinished
    


    #
    # Setters
    def set_player_user(self, player, user):
        if player in self.players:
            self.players[player] = user
            return True
        return False

    def start(self):
        # Remove the players that have not been chosen
        [self.players.pop(playerToRemove, None) for playerToRemove in [player for player in self.players if self.players[player] == None]]

        # Only allow 2, 3 and 4 player games
        if len(self.players) not in [2, 3, 4]: return False

        # Get the number of cards that each player will have (depends on the number of players)
        self.cardsPerPlayer = {2:7, 3:5, 4:4}[len(self.players)]

        # Give each player as many cards as he needs
        for player in self.players:
            self.deal_cards_player(player)

        # Start the game (in the header phase)
        self.isHeaderPhase = True
        self.isStarted = True

        return True

    def finish(self):
        self.isFinished = True
    
    #
    # Helper functions
    def deal_cards_player(self, player):
        cards = []

        # Get the current number of cards of the player
        cardsPlayer = len(requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}').json())

        # If the main deck has less than self.cardsPerPlayer-cardsPlayer cards, put the discarded cards back into the main deck
        if len(requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()) < self.cardsPerPlayer - cardsPlayer:
            logger.debug(f'There are not enough cards in the main deck to be able to deal to player {player}, shuffleling discarded deck into the main deck')
            for card in requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded').json():
                requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/' + str(card['id']))
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/' + str(card['id']))

        # If the current round is round 5 and there are no cards of the post era in the main deck, add them to it
        mainDeckCards = [card['id'] for card in requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main').json()]
        postEraCards = [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88] #100?
        if not any (card in postEraCards for card in mainDeckCards) and requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] == 5:
            logger.debug('Round 5, shuffleing post era cards into the main deck')
            for card in postEraCards:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/{card}')

        # Call the main deck self.cardsPerPlayer times in random order and get the first card
        for i in range(0, self.cardsPerPlayer - cardsPlayer):
            card = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()[0]['id']

            # Cannot have the same card twice
            while card in cards:
                card = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main?random=True').json()[0]['id']
            
            cards.append(card)

        # Remove those cards from the main deck and add them to the player's hand
        for card in cards:
            requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/main/{card}')
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/{card}')
    
    def is_players_turn(self, player):
        if len(self.playingOrderCurrent) > 0 and self.playingOrderCurrent[0] == player:
            return True
        return False
    
    def is_player_with_edge(self, player, country):
        if country['influence'] == {}:
            return False
        else:
            # Get the influence of the player
            influence = country['influence'].get(player, {'influence': 0})['influence']

            # Check if another player has more or the same influence
            for anotherPlayer in [eachPlayer for eachPlayer in country['influence'] if eachPlayer != player]:
                if country['influence'][anotherPlayer]['influence'] >= influence:
                    return False
            
            return True

    def is_another_player_with_edge(self, player, country):
        if country['influence'] == {}:
            return False
        else:
            # Get the influence of the player
            influence = country['influence'].get(player, {'influence': 0})['influence']

            # Check if another player has more influence
            for anotherPlayer in [eachPlayer for eachPlayer in country['influence'] if eachPlayer != player]:
                if country['influence'][anotherPlayer]['influence'] > influence:
                    return True
            
            return False
    
    def increment_player_score(self, player, increment):
        score = self.board_score_get()
        
        # Increment the score
        if increment !=0:
            for eachPlayer in score:
                if eachPlayer['name'] == player:
                    eachPlayer['score'] = eachPlayer['score']+increment
        
                    # If score is negative, share the VP among the rest of the players, starting from the player of his block if any
                    if eachPlayer['score'] < 0:
                        logger.info("Negative score! Sharing...")
                        rest = eachPlayer['score'] * -1
                        eachPlayer['score'] = 0

                        # Sort the players from lowest to highest score
                        score = sorted(score, key=lambda x: x['score'])

                        # Start from your block if any
                        for key, val in {'US': 'EU', 'EU': 'US', 'China': 'Russia', 'Russia': 'China'}.items():
                            if player == key and val in self.playingOrder:
                                startingPlayer = next(filter(lambda x: x['name'] == val, score))
                                score = list(filter(lambda x: x['name'] != val, score))
                                score.insert(0, startingPlayer) # https://stackoverflow.com/questions/17911091/append-integer-to-beginning-of-list-in-python

                        # Add the points
                        while rest > 0:
                            for eachPlayer in range(0, len(score)):
                                score[eachPlayer]['score'] += 1
                                rest -= 1
                                if rest < 1: break
                        
                        # Update the scores
                        for eachUpdatedPlayer in score:
                            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/' + eachUpdatedPlayer['name'], json={'score': eachUpdatedPlayer['score']})
                    else:
                        # Update the score of the player
                        requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score/{player}', json={'score': eachPlayer['score']})
                        
    def handle_players_card(self, player, card):
        id = card['id']
        # Remove the card from the player's hand
        requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/{id}')
        
        # Remove the card from the player's header (if header == card)
        if self.cards_player_get(player)[player]['header'] == id:
            requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header')

        # If the card has to be kept on the board, send it to playing
        if card['inPlay'] == True:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/{id}')
        else:
            # If card['remove'] == true, send card to the removed deck, otherwise send to the discarded deck
            if card['remove'] == True:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/removed/{id}')
            else:
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/{id}')

    def endRound(self):
        logger.info('END ROUND --------------------------')
        inplay = self.cards_playing_get()

        #Remove from inplay to discard
        for card in inplay:
            if card==2 or card==16: #antiglobalization or g20 - send to discard from inplay
                requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/{card}')
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/{card}')
            if card==9: #EFTA - send to remove from inplay in turn 6
                if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] == 5:
                    country=utils.getCountry(self, "Norway")
                    country["isOilProducer"]=False
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Norway', json=country)
                    requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/{card}')
                    requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/removed/{card}')
            if card==27: #Neoliberalism 
                #TODO: keep the count and remove 1 influence
                requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/{card}')
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/{card}')
                                    
        return
        
    #Gestiona la carta jugada con respecto a los mazos
    def handle_players_play(self, player):
        logger.info('\n\n\nHANDLE PLAYERS PLAY --------------------------')
        logger.info('handle_players_play(): ' + f'Called with player={player}')
        
        #1) Pass the turn if there are players left
        if len(self.playingOrderCurrent) > 0:
            logger.info('handle_players_play(): ' + 'Popping out current player')
            self.playingOrderCurrent.pop(0)
    
        #2) If there are no players left to play in this turn
        logger.info('handle_players_play(): Playing order current: ' + str(self.playingOrderCurrent))
        if len(self.playingOrderCurrent) == 0:
            logger.info('handle_players_play(): ' + 'There are no players left to play')
            
            # Always reconstruct the playing order
            logger.info('handle_players_play(): ' + 'Reconstructing the playing order')
            if len(self.playingOrderCurrent) == 0:
                self.playingOrderCurrent = [eachPlayer for eachPlayer in self.playingOrder]
                logger.debug('handle_players_play(): ' + f'New playing order: {str(self.playingOrderCurrent)}')

            #2) If in the postHeaderPhase
            if self.isHeaderPhase == False:
                self.numSubRounds+=1
                
                if(self.numSubRounds==2):
                    # If round == 8, finish the game
                    if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] >= 8:
                        logger.debug('handle_players_play(): Finishing the game')
                        return self.finish()
                    
                    logger.info('handle_players_play(): ' + 'Starting a new round')
                    # New round must begin
                    requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round')
    
                    # Deal each player as many cards as he needs
                    for eachPlayer in self.players:
                        logger.info('handle_players_play(): ' + f'Dealing cards to player {eachPlayer}')
                        self.deal_cards_player(eachPlayer)
                    
                    #Remove cards in play that are temporary
                    self.endRound()
                    
                    # Start the next round in the header phase
                    logger.info('handle_players_play(): Setting the header phase')
                    self.isHeaderPhase = True
                    
            #3) If header phase, end it
            else:
                logger.info('handle_players_play(): Finishing the header phase')
                self.isHeaderPhase = False
                self.numSubRounds=0


    #
    # Logic functions
    def card_get(self, id):
        response = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/{id}')
        return response.json()
    
    def cards_player_get(self, requestingPlayer):
        # Prepare the cards object
        cards = {}
        
        for player in [player for player in self.players if self.players[player]!=None]:
            cards[player] = {'header': None, 'hand': []}
        
        # Obtain the cards of all players
        for player in cards:
            # Only show the hand of the requesting player
            if player == requestingPlayer:
                hand = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}').json()
                [cards[player]['hand'].append(card['id']) for card in hand]

            # Get all the headers 
            header = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()
            if header['id'] != None:
                cards[player]['header'] = header['id']

        # Remove cards if we are not in the header phase and if everyone has header=null
        if self.get_isHeaderPhase() == True or len([player for player in cards if cards[player]['header'] == None]) == len(self.playingOrder):
            for player in cards:
                if player != requestingPlayer: cards[player]['header'] = None

        return cards
    
    def cards_deck_get(self, type):
        if(type=="main"):
            logger.info("ERROR: main deck cannot be inspected")
            return False
        deck = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/{type}').json()
        return deck
    
    def cards_playing_get(self):
        playing = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
        return [card['id'] for card in playing]

    def board_round_get(self):
        return requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()
    
    def board_score_get(self):
        score = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/score').json()
        
        # Only show the score of the players of the game. e.g: IF there are 3 players, do not show 4 scores
        score = [playerScore for playerScore in score if playerScore['name'] in [player for player in self.players if self.players[player] != None]]
        return score

    def board_map_get(self):
        return requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board').json()
    
    
    def cards_playing_delete(self, player, id):
        result=requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}//game/{self.id}/cards/playing/{id}')
        result=requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}//game/{self.id}/cards/deck/removed/{id}')
        return result
    
    def cards_playing_header_set(self, player, id):
        requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header/{id}')

        # Check if all the players have their header cards set
        count = len(self.players)
        for player in self.players:
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id'] != None:
                count -= 1

        # If so,
        if count == 0:
            # End the header phase and start the postheader phase
            #self.isHeaderPhase = False
            #self.isPostHeaderPhase = True

            # Set the playing order
            order = []
            self.playingOrder = []
            self.playingOrderCurrent = []
            for player in self.players:
                header = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/player/{player}/header').json()['id']
                header = self.card_get(header)['points']
                order.append({'player': player, 'points': header})

            for card in sorted(order, key=lambda x: x['points'])[::-1]:
                self.playingOrder.append(card['player'])
                self.playingOrderCurrent.append(card['player'])
            #TODO: resolve header cards text in order. -> to do separately on frontend, so by now header phase not ended here

    def cards_play_influence(self, player, id, body, validate=False):
        logger.info(f"\n\n{player} plays {id} for influence\n\n")
        # If not the player's turn
        if self.is_players_turn(player) == False: 
            logger.info(f"It is not {player}'s turn")
            logger.info(f"{self.playingOrderCurrent}")
            return False

        # Check if the card exists
        card = self.card_get(id)
        if card == {}: 
            logger.info(f"Card {id} does not exist")
            return False

        #logger.info("Getting countries...")
        # Get all the countries of the map
        countriesAll = self.board_map_get()['countries']
        
        #
        # Count all the points that the user wants to use
        #logger.info("Counting points...")
        pointCount = 0
        cont={} #for possible edge breakings
        for target in body['targets']:
            #logger.info(f"Target is {target}")
            # Get the name and the object of the country
            targetName = next(iter(target['target'])) # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
            logger.info(f"Target name is {targetName}")
            targetObject = next(filter(lambda x: x['name'] == targetName, countriesAll))
            logger.info(f"Target object is {targetObject}")

            if not utils.isAdjacentOrWithInfluence(self, targetObject, player,logger):
                logger.info(f"No valid country {targetName}")
                return False
            logger.info("Target is valid")
            
            # Count the influence points + stability of the country
            cost=targetObject["stability"]
            # Count if another player has the edge (more influence than the actual player)
            ec=utils.whoEdges(self,targetName,logger)
            if(ec!="" and ec!=player):
                edgeBreak=False
                if(targetName in cont): #check edgeBreak
                    playerInfluence=0
                    if(player in targetObject["influence"]):
                        playerInfluence+=targetObject["influence"][player]["influence"]
                    if(playerInfluence+cont[targetName]>=targetObject["influence"][ec]["influence"]):
                        edgeBreak=True
                if(not edgeBreak):
                    cost += 1
                if not targetName in cont:
                    cont[targetName]=1
                else:  #second or more influence in the country
                    cont[targetName]+=1
            pointCount += target['target'][targetName]*cost
            logger.info(f"Point count is {pointCount}")
            
            # If extra target was specified, count those points too
            #TODO: all targetExtra stuff is not complete (nothing done on frontend)
            if target['targetExtra'] != None:
                for extraTarget in target['targetExtra']:
                    # A player cannot have extra influence on himself
                    if extraTarget == player: 
                        return False
                    pointCount += target['targetExtra'][extraTarget]*cost
        logger.info(f"Total point count is {pointCount} and card points is {card['points']}")
        
        opMods=utils.getOpsModifiers(self, card, player, "influence", use=body["used"]) 
        if(card["points"]+opMods < pointCount):
            #NOTE: it does not have into account that you can break edge after the first point
            logger.info(f"INFLUENCE: ERROR: {pointCount} points spent are higher than {card['points']}+{opMods}")
            return False
        
        # Apply modifications to each country (if there are no prohibitions)
        logger.info("Applying modifications to countries...")
        countries = {}
        for target in body['targets']:
            targetName = next(iter(target['target']))
            targetObject = next(filter(lambda x: x['name'] == targetName, countriesAll))
            logger.info(f"\tAdding influence to {targetName}")
            # Add the country to the list of countries
            countries[targetName] = targetObject
            
            #Checking prohibitions
            logger.info(f"Checking prohibitions {countries[targetName]['comments']}")
            prohibited=False
            if(countries[targetName]["comments"]!="" and countries[targetName]["comments"][0]=="{"):
                comments=json.loads(countries[targetName]["comments"])
                if("no influence" in comments and player in comments["no influence"]):
                    prohibited=True
                    
            # Initialize the country if empty
            if countries[targetName]['influence'].get(player, None) == None:
                countries[targetName]['influence'][player] = {'influence': 0, 'extra': {}}

            influencePointsToSum = target['target'][targetName]
            logger.info(f"\t Adding {influencePointsToSum} points")
            # Check if there is another player with extra influence over this player. If one slot is occupied, can only occupy the other. If both slots are occupied, cannot play influence or destabilization ops at all
            influencePointsUsed = 0
            for eachPlayer, eachInfluence in countries[targetName]['influence'].items():
                # Sum the extra influence of other players over this player
                if 'extra' in eachInfluence:
                    if player in eachInfluence['extra']:
                        influencePointsUsed += eachInfluence['extra'][player]
            logger.info(f"\tSpaces occupied by this player on other superpowers' spaces': {influencePointsUsed}")
            
            # Check if the current influence + the extra influence from other players + the influence to sum is > 2
            if countries[targetName]['influence'][player]['influence'] + influencePointsUsed + influencePointsToSum > 2: 
                logger.info("INFLUENCE: sum of influence greater than 2")
                #TODO: the extra influence should go to another superpowers' spaces.
                #return False

            # Modify the player's influence over the country using the request body
            if not prohibited:
                countries[targetName]['influence'][player]['influence'] += influencePointsToSum

                logger.info(f"\tModify extra influence")
                # Modify the extra influence of the country using the request body
                if target['targetExtra']:
                    for extraTarget in target['targetExtra']:
                        # Check if the country has x influence so x+target['targetExtra'][extraTarget] is <=2
                        if countries[targetName]['influence'].get(extraTarget, {'influence': 0, 'extra': {}})['influence'] + target['targetExtra'][extraTarget] > 2: return False
    
                        # Add the extra influence
                        countries[targetName]['influence'][player]['extra'] = {extraTarget: target['targetExtra'][extraTarget]}
            else:
                logger.info("This country is prohibited for this player for influence")
        #
        # If only validate, return here
        if validate == True: return True
        logger.info("Update targets in server...")
        # If all went good, update the countries in the resources service
        for eachCountry in countries:
            logger.info(f'{eachCountry}')
            logger.info(f'{countries[eachCountry]}')
            response=requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{eachCountry}', json=countries[eachCountry])
            logger.info(f"RESPONSE IS {response.json()}")
            
        logger.info("Wrap up hand and deck...")
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        logger.info("Card played successfully")
        return True

    def cards_play_destabilization(self, player, id, body, validate=False, wrap=True):
        # If not the player's turn
        if(wrap):
            if self.is_players_turn(player) == False: return False
        elif id not in [12,85]:
             #Only cards 12 (EMPIRE OF WAR) and 85 (MOTHER OF ALL WARS) allow unwrapped destabilizations
             #Actually, only card 12 if played as header by East, but we
             #keep both in case the above wrapping evolves to catch destabilization on headers, etc.
             logger.info("ERROR: DESTABILIZATION: attempting unwrapped with wrong card (only card 12 allowed)")
             return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False
    
        # Check that the requested country exists and get its data
        # The target country cannot be a country that belongs to another player
        name = body['target']
        logger.info(f"DESTABILIZATION for {player} in {name}")
        if name in ['United States', 'Russia', 'China'] or name in self.UEmembers: 
            logger.info("ERROR: Cannot destabilize a superpower")
            return False

        country=utils.getCountry(self, name)
        # There has to be influence from another player
        if country['influence'] == {} or len([anotherPlayer for anotherPlayer in country['influence'] if anotherPlayer != player]) == 0: 
            logger.info("ERROR: must be influence from another player")
            return False

        #
        # If this is the first request
        if self.destabilization == None:
            logger.info("Dice roll")
            # Do the dice throw and all the operations
            #TODO: add card modifiers based on NWO, etc.
            diceRoll = random.choice([1, 2, 3, 4, 5, 6]) + card['points'] - country['stability'] * 2

            # If the country is conflictive, lose 1 VP
            #(except some special cases: Drones and War on Terror and Mother of All Wars)
            if country['isConflictive'] == True:
                logger.info("Checking NWO")
                nwo = self.board_map_get()["nwo"]
                if(id!=85): #mother of all wars is exempt
                    logger.info(f"Checking drones {nwo}")
                    if nwo["Technology"]["Drones"]["supremacy"]!=player:
                        logger.info("Checking war on terror...")
                        inplay=requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
                        logger.info(f"Cards in play {inplay}")
                        if(not 88 in inplay):
                            self.increment_player_score(player, -1)
                        elif(player!="US" or (not country["region"] in ["Middle East", "Africa"])):
                            self.increment_player_score(player, -1)
                    
            # If only validate
            if validate == True:
                return diceRoll
            
            logger.info(f"dice roll is {diceRoll}")
            # If player was lucky
            if diceRoll > 0:
                # Set self.destabilization
                self.destabilization = {'country': country['name'], 'result': diceRoll}
                # Do not remove the player's card or do anything with the turn
            else:
                # The player lost this card, so we continue with the game
                if(wrap):  
                    logger.info("WRAPPING UP because of roll<=0")
                    # Handle the player's played card
                    self.handle_players_card(player, card)
    
                    # Handle the player's play
                    self.handle_players_play(player)

            # Return the result of the dice throw
            return diceRoll
        
        #
        # If this is the second request
        else:
            logger.info("Second request")
            if self.destabilization['country'] != body['target']: 
                logger.info(f"ERROR: Not the same country {self.destabilization['country']} vs {body['target']}!")
                return False
            
            logger.info(f"Applying results to {country}...")
            for target in body["targets"]:
                logger.info(f"\t{target}")
                if target==player:
                    if not target in country['influence']:
                        country["influence"][target]={"influence":0, "extra":{}}
                    country["influence"][target]["influence"]+=1
                else:
                    if country['influence'][target] != None:
                        if country["influence"][target]["influence"]>0:
                            country["influence"][target]["influence"]-=1
                        else:
                            logger.info("DESTABILIZATION ERROR: no influence to remove")
                            return False
                    else:
                        logger.info("DESTABILIZATION ERROR: no influence key to remove")
            
            # Cannot spend more points than diceRoll
            #if len(pointCount > self.destabilization['result']: 
            if len(body["targets"]) > self.destabilization['result']: 
                logger.info("Too many points spent")
                return False
            
            #
            # If only validate
            if validate == True: return True


            # Update the country
            logger.info("Updating country...")
            countryName = country['name']
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{countryName}', json=country)
            
            # Unset the destabilization for the next destabilization play
            self.destabilization = None
            
            if(wrap):
                # Handle the player's played card
                self.handle_players_card(player, card)
    
                # Handle the player's play
                self.handle_players_play(player)
            
        return True

    def cards_play_text(self, playingPlayer, id, body, wrap=True):
        logger.info(f'\n\n\nCARDS_PLAY_TEXT_START: {id}')
        # If not the player's turn or (header card is set and is trying to play another one), error out
        if(wrap):
            body=json.loads(body.json())
            if self.is_players_turn(playingPlayer) == False:
                logger.info(f'Incorrect turn {self.is_players_turn(playingPlayer)}')
                return False
            elif self.cards_player_get(playingPlayer)[playingPlayer]['header'] != None: 
                if (self.isHeaderPhase and self.cards_player_get(playingPlayer)[playingPlayer]['header'] in self.cards_player_get(playingPlayer)[playingPlayer]["hand"]) and self.cards_player_get(playingPlayer)[playingPlayer]['header'] != id: 
                    logger.info(f"It is header phase and it's trying to use a card different to the one declared as header")
                    return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}:
            logger.info(f"ERROR: PLAY TEXT: Card {id} does not exist");
            return False

        if not wrap:#It only happens for Embassy Asylum (card 12), so this card should be a Personality
            if card["type"]!="Personalty":
                if not "subtype" in card.keys() or card["subtype"]!="Personality":
                    logger.info("ERROR: card played with EMBASSY ASYLUM should be a Personality")
                    return False
        ########################################################################
        # Carry out the pertinent operations according to the card ------------------------------------------
        ########################################################################
        #UNDER CONSTRUCTION
        underConstruction=False
        if underConstruction:
            self.handle_players_card(playingPlayer, card)
            self.handle_players_play(playingPlayer)
            return True
        #UNDER CONSTRUCION
        
    
        logger.info('CHOOSING CARD>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        logger.info(f"{body}")
        player=body["resolvingPlayer"]
        
        if card['id'] == 1: #ANGOLAN CIVIL WAR
            # Roll a dice
            diceRoll = utils.roll()

            if logger!=None: logger.info(f"Roll {diceRoll}")
            # Get what we have to subtract
            for country in utils.getCountry(self, "Angola")["adjacent"]:
                if logger!=None: logger.info(f"\tCountry: {country}")
                we=utils.whoEdges(self, country, logger)
                if(we!=player and we!=""):
                    diceRoll-=1

            # If modified dice throw in 3-6
            logger.debug(f'Modified dice throw: {diceRoll}')
            if diceRoll >= 3:
                # Gain 1 VP
                self.increment_player_score(player, 1)

                logger.info("Removing influence for other powers")
                for power in ["US","EU","Russia", "China"]:
                    if(power!=player):
                        utils.addInfluence(self, "Angola", player, -1)
                logger.info("Edging country")
                utils.edgeCountry(self, "Angola", player)
                    
        
        #ANTI-GLOBALIZATION MOVEMENT
        elif card['id'] == 2:
            #ongoing on utils.getOpsModifiers and on endRound
            pass
        
        #BLACK MONDAY
        elif card['id'] == 3:
            board = self.board_map_get()
            logger.debug(f'Getting board with keys {board.keys()}')
            logger.debug(f'Getting nwo with keys {board["nwo"].keys()}')
            
            for nwo in board["nwo"]["Economy"].values():
                if nwo["supremacy"]=="EU" or nwo["supremacy"]=="US":
                    nwo["supremacy"]==""
                    
            logger.debug('Finishing black monday')
                    
        #BORIS YELTSIN
        elif card['id'] == 4:
            utils.addInfluence(self, "Russia", "US", 1, logger)
            
            
        #CHECHEN WARS 
        elif card['id'] == 5:
            if player == "Russia":
                utils.edgeCountry(self, "Caucasus States", "Russia",logger)
                self.increment_player_score("Russia", -1)
            else:
                logger.info("Removing edge from Russia in Caucasus")
                utils.removeEdge(self, "Caucasus States", "Russia", logger)
        
        #CONGO WARS
        elif card['id'] == 6: #exact code to cardid=1 but no VP gains
            # Roll a dice
            diceRoll = utils.roll()

            if logger!=None: logger.info(f"Roll {diceRoll}")
            # Get what we have to subtract
            
            for country in utils.getCountry(self, "Congo")["adjacent"]:
                if logger!=None: logger.info(f"\tCountry: {country}")
                we=utils.whoEdges(self, country, logger)
                if(we!=player and we!=""):
                    diceRoll-=1

            # If modified dice throw in 3-6
            logger.debug(f'Modified dice throw: {diceRoll}')
            if diceRoll >= 3:
                
                logger.info("Removing influence for other powers")
                for power in ["US","EU","Russia", "China"]:
                    if(power!=player):
                        utils.addInfluence(self, "Congo", player, -1)
                logger.info("Edging country")
                utils.edgeCountry(self, "Congo", player)
            
        #DEMOCRACY IN NIGERIA
        elif card['id'] == 7:
            self.increment_player_score(player, 1)
            
            country=utils.getCountry(self, "Nigeria")
            country["stability"]=2
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
            utils.addInfluence(self, "Nigeria", player, 1, logger)
            
        #ECONOMIC CRISIS    
        elif card['id'] == 8:
            tc=body["targets"][0]
            country=utils.getCountry(self,tc)
            prem=body["players"][0]
            padd=body["players"][1]
            logger.info(f"Removing {prem} and addin {padd} to {tc}")
            
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] <= 4:
                logger.info("Pre 9/11")
                #remove 1 E influence from a country, then add 1 W 
                if(prem not in ["Russia", "China"] and padd not in ["EU","US"]):
                    logger.info("ERROR: incorrect blocks")
                    return False
            else:
                logger.info("Post 9/11")
                if(padd not in ["Russia", "China"] and prem not in ["EU","US"]):
                    logger.info("ERROR: incorrect blocks")
                    return False
            utils.addInfluence(self,tc,prem,-1)
            utils.addInfluence(self,tc,prem,1)
            
        #EFTA AGREEMENT
        elif card['id'] == 9:
            utils.addInfluence(self, "Norway", "EU", 1, logger)
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] < 6:
                country=utils.getCountry(self, "Norway")
                country["isOilProducer"]=True
                requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Norway', json=country)
            
        #EL JEFE
        elif card['id'] == 10:
            utils.addInfluence(self, "Cuba", "China", 1, logger)
            utils.addInfluence(self, "Cuba", "Russia", 1, logger)
            
            #Veto to US influence
            country=utils.getCountry(self, "Cuba")
            country["comments"]='{"no influence":["US"]}'
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
        #EMBASSY ASYLUM    
        elif card['id'] == 11:
            if(body["operation"]!=""):
                newCard=body["operation"]
                self.cards_play_text(playingPlayer, newCard, body, wrap=False)
            else:
                logger.info("ERROR: no card specified")
                #return False
                #it is allowed to play it without target
        #EMPIRE OF WAR
        elif card['id'] == 12:
            #TODO: make 1+1 destabilizations
            if(player=="US"):
                #1st destabilization: (TODO: make the second one)
                logger.info("THE EMPIRE OF WAR")
                ret=self.cards_play_destabilization(player, id, body={"target":body["targets"][0], "targets":body["players"]}, validate=False, wrap=True)
                logger.info(f"RETURNING {ret}")
                return ret #returns the dice roll result (no need for wrapping, is was either done if unsuccessful, it will be done on second call if successful)
                
                #logger.debug("TODO")
                #targets should have both target countries
                #players by now should have 
                #if(len(body["targets"])==2):
                #    cards_play_destabilization(self, player, id, body={"target":body["targets"][0], "players":}, validate=False, wrap=False)
                
        #EUROPE (DONE)
        elif card['id'] == 13:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
   
        #FALL OF THE BERLIN WALL 
        elif card['id'] == 14:
            utils.addInfluence(self, "Germany", "Russia", -1, logger)
            if(len(body["players"])==1):
                utils.addInfluence(self, "Germany", body["players"][0], 1)
            else:
                logger.info("ERROR: no target for Berling Wall")
            self.increment_player_score("US", 1)
            if(player=="China" or player=="Russia"):
                self.increment_player_score("US", 1)
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] <= 4:
                self.increment_player_score("US", 1)
         
        #FSB CREATION
        elif card['id'] == 15:
            utils.addInfluence(self, "Russia", "Russia", 1, logger)
            #ongoing on frontend
            
        #G20
        elif card['id'] == 16:
            if(len(self.players)==4):
                self.g20={"player":2}
            else:
                self.g20={"player":1}
            #ongoing done in utils.getOpsModifiers
            #TODO: make ongoing in frontend
            
        #IMF INTERVENTION
        elif card['id'] == 17:
            logger.debug("TODO")
        
        #IMMIGRANTS
        elif card['id'] == 18:
            country=body["targets"][0]
            if(country in self.UEmembers or country in ["United States", "Canada"]):
                logger.info(f"Valid target {country}")
            else:
                logger.info("ERROR: Country is not US, Canada or UE")
                #return False
            
            if(body["operation"]=="prevent"):
                lp=utils.whoEdges(self,body["targets"][0],logger)
                logger.info(f"Remove 2VP from {lp}")
                if(lp!=""):
                    self.increment_player_score(lp, -2)
                else:
                    logger.info("ERROR: IMMIGRANTS: No player with edge to negate the card")
                    #return False
            else:
                utils.addInfluence(self, country, player, 1, logger)
                
         
            logger.debug("TODO")
        
        #ISRAELI-PALESTINIAN WARS
        elif card['id'] == 19:
            # Roll a dice
            diceRoll = utils.roll()

            if logger!=None: logger.info(f"Roll {diceRoll}")
            # Get what we have to subtract
            
            for country in utils.getCountry(self, "Israel")["adjacent"]:
                if logger!=None: logger.info(f"\tCountry: {country}")
                we=utils.whoEdges(self, country, logger)
                if(we!="US"):
                    diceRoll-=1

            # If modified dice throw in 3-6
            logger.debug(f'Modified dice throw: {diceRoll}')
            if diceRoll <= 1:
                logger.info("1 VP for other powers")
                for power in ["EU","Russia", "China"]:
                    self.increment_player_score(power, 1)
                utils.addInfluence(self, "Israel", "US", -1, logger)
                if(len(body["targets"])==1):
                    if(body["targets"][0] in utils.getCountry(self, "Israel")["adjacent"]):
                        utils.addInfluence(self, body["targets"][0], "US", -1, logger)
                    else:
                        logger.info("ERROR: Country not adjacent to Israel")
                        return False
            
        #KATRINA
        elif card['id'] == 20:
            self.increment_player_score("US", -1)
        
        #KHOBAR TOWERS ATTACK
        elif card['id'] == 21:
            if(body["targets"][0] in ["EU", "US"]):
                utils.addInfluence(self, "Saudi Arabia", body["targets"][0], -1)
            else:
                logger.info("ERROR: Khobar Towers: influence to remove must be from west")
                return False
            
        #MAASTRICH TREATY
        elif card['id'] == 22:
            self.increment_player_score("EU", 1)
            options=["Germany", "France", "Italy", "Spain-Portugal", "Benelux", "Denmark", "Greece"]
            if(len(body["targets"])==2):
                for t in body["targets"]:
                    if t in options:
                            utils.addInfluence(self, t, "EU", 1, logger)
                    else:
                        return False #no valid country
            else:
                return False #no valid # of countries
            
        #MADE IN CHINA
        elif card['id'] == 23:
            utils.addInfluence(self, "United States", "China", 1, logger)
            if("targets" in body.keys() and len(body["targets"])==2):
                logger.info("Conditions met")
                anyCountry=0
                for target in body["targets"]:
                    logger.info(f"Adding influence to {target}")
                    if target in self.UEmembers:
                        utils.addInfluence(self, target, "China", 1, logger)
                    elif target!="US" and anyCountry==0:
                        utils.addInfluence(self, target, "China", 1, logger)
                        anyCountry+=1
                    else:
                        return False #more than one free country chosen
            
        #MIDDLE EAST
        elif card['id'] == 24:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
   
        #MUAMMAR GADDAFI
        elif card['id'] == 25:
            utils.addInfluence(self, "Libya", player, 1, logger)
            
            #Country specifics
            country=utils.getCountry(self, "Libya")
            country["isOilProducer"]=True
            country["comments"]='{"no destabilization":["US", "EU", "Russia", "China"]}'
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
        
        #NEOCOLONIALISM
        elif card['id'] == 26:
            self.increment_player_score("EU", -1)
            self.increment_player_score("US", -1)
            logger.info("Two decrements ok")
            if("options" in body.keys() and len(body["options"])==1):
                self.increment_player_score(body["options"][0], -1)
            logger.info("Third decrement ok")
                
            if("targets" in body.keys() and len(body["targets"])==2 and "players" in body.keys() and len(body["players"])==2):
                us=0
                eu=0
                logger.info("Conditions met")
                for k in range(len(body["targets"])):
                    logger.info(f"Target {k}")
                    target=body["targets"][k]
                    p=body["players"][k]
                    logger.info(f"{target}")
                    logger.info(f"{p}")
                    if(p=="US" and us==0):
                        utils.addInfluence(self, target, p, 1, logger)
                        us=1
                    elif(p=="EU" and eu==0):
                        utils.addInfluence(self, target, p, 1, logger)
                        eu=1
                        
        #NEOLIBERALISM
        elif card['id'] == 27:
            utils.addInfluence(self, body["targets"][0], player, 2, logger)

        #NORTHERN ADHESION
        elif card['id'] == 28:
            self.increment_player_score("EU", 1)
            logger.info("+1 point to EU")
            adhesion=["Austria", "Finland", "Sweden"]
            for k in adhesion:
                self.UEmembers.append(k)
            logger.info("Members added")
            
            if(len(body["targets"])==1 and body["targets"][0] in adhesion):
                logger.info("Adding 1 to")
                logger.info(f"{body['targets']}")
                utils.addInfluence(self, body["targets"][0], "EU", 1, logger)
                
            
        #OIL CRISIS    
        elif card['id'] == 29:
            #ongoing, controlled in cards_play_score
            pass
        
        #OIL THIRST
        elif card['id'] == 30:
            logger.debug("TODO")
        
        #OPEC
        elif card['id'] == 31:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
            # for country in self.board_map_get()['countries']:
            #     if country["isOilProducer"]:
            #         ce=utils.whoEdges(self,country["name"],logger)
            #         if(ce!=None):
            #             self.increment_player_score(ce, 1)
            #             if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] > 4:
            #                 self.increment_player_score(ce, 1)
            # for k in ["US","EU","China","Russia"]:
            #     self.increment_player_score(k, -2)
            #     if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] > 4:
            #         self.increment_player_score(k, -2)

        #OSAMA BIN LADEN            
        elif card['id'] == 32:
            #TODO: ability to influence on middle east/afghanistan
            if(len(body["targets"])>0 and len(body["players"])>0):
                logger.info("Removing influence")
                utils.addInfluence(self, body["targets"][0], body["players"][0], -1, logger)
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] >= 5:
                logger.info("Removing US influence")
                if(len(body["targets"])==2 and len(body["players"])==2 and body["players"][1]=="US"):
                    utils.addInfluence(self, body["targets"][1], body["players"][1], -1, logger)
                logger.info("Removing US VP")
                self.increment_player_score("US", -1)

                    

        #PARTY CONGRESS
        elif card['id'] == 33:
            if("targets" in body.keys()):
               if(len(body["targets"])==1 and body["targets"][0] not in self.superpowers and body["targets"][0] not in self.UEmembers):
                   if logger!=None: logger.info("One country")
                   utils.addInfluence(self, body["targets"][0], "China", 1, logger)
               elif(len(body["targets"])==3):
                    if logger!=None: logger.info("Three countries")
                    regions=[]
                    for t in body["targets"]:
                        regions.append(utils.getCountry(self, t)["region"])
                    if logger!=None: logger.info(f"Regions: {regions}")
                    if(len(set(regions))<3):
                        return False #must be different regions
                    
                    if logger!=None: logger.info("Changing influence...")
                    utils.addInfluence(self, "China", "China", -1, logger)
                    for t in body["targets"]:
                        utils.addInfluence(self, t, "China", 1, logger)
                        
               else: #must have 1 or 3 targets
                    return False
            else:
                return False
             
        #PETRODOLLARS  
        elif card['id'] == 34:
            board = self.board_map_get()
            if board["nwo"]["Economy"]["Fiscal paradises"]["supremacy"]==None:
                board["nwo"]["Economy"]["Fiscal paradises"]["supremacy"]=player
            else:
                board["nwo"]["Economy"]["Fiscal paradises"]["supremacy"]=None
            
            if board["nwo"]["Economy"]["Sovereign funds"]["supremacy"]==None:
                board["nwo"]["Economy"]["Sovereign funds"]["supremacy"]=player
            else:
                board["nwo"]["Economy"]["Sovereign funds"]["supremacy"]=None
                
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/Sovereign funds', json=board['nwo']["Economy"]["Sovereign funds"])
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/Fiscal paradises', json=board['nwo']["Economy"]["Sovereign funds"])
            
               
        #RUPERT MURDOCH        
        elif card['id'] == 35:
            logger.info("RUPERT MURDOCH--------------------------")
            board = self.board_map_get()
            logger.info("board ok")
            if("targets" in body.keys()):
               po=board["nwo"]["Public opinion"]
               logger.info("Checking targets")
               if len(body["targets"])<=2:
                  for t in body["targets"]:
                    logger.info(f"target {t}")
                    if(t in po.keys()):
                        po[t]["supremacy"]="US"
                        requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Public opinion/{t}', json=board['nwo']["Public opinion"][t])
                    else:
                        logger.info("Invalid NWO slot")
                        return False #must be a valid public opinion slot
               else: #must have <3 targets
                    logger.info("Too many targets (max 2)")
                    return False
            else:
                logger.info("targets is empty or something else")
                return False

            
        #RUSSIAN OLIGARCHS
        elif card['id'] == 36:
            board = self.board_map_get()
            if("targets" in body.keys()):
                if len(body["targets"])==1:
                    board["nwo"]["Economy"][body["targets"][0]]["supremacy"]="Russia"        
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/{body["targets"][0]}', json=board['nwo']["Economy"][body["targets"][0]])
                else:
                    return False
            else:
                return False
            
        #RWANDAN GENOCIDE    
        elif card['id'] == 37:
            self.increment_player_score("US", -1)
            self.increment_player_score("EU", -1)
            for i in body["players"]:
                if(i in ["EU", "US"]):
                   self.increment_player_score(i, -1)
                   utils.addInfluence(self, "Congo", i, 2, logger)
            
        #SHOCK DOCTRINE
        elif card['id'] == 38:
            board = self.board_map_get()
            if("operation" in body.keys() and "targets" in body.keys()):
               if(body["operation"]=="remove"):
                  if(len(body["targets"])<=2):
                      for t in body["targets"]:
                          board["nwo"]["Economy"][t]["supremacy"]=None
                          requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/{t}', json=board['nwo']["Economy"][t])
                    
                  else:
                      return False #maximum 2 targets
               elif(body["operation"]=="add"):
                    board["nwo"]["Economy"][body["targets"][0]]["supremacy"]=player
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/{body["targets"][0]}', json=board['nwo']["Economy"][body["targets"][0]])
               else:
                    return False #undefined operation
            else:
                return False #body must contain operation and targets
        
        #SLOBODAN MILOSEVIC
        elif card['id'] == 39:
            utils.addInfluence(self, "Balkan States", "Russia", 1, logger)
            utils.addInfluence(self, "Balkan States", "China", 1, logger)
        
        #SOMALI CIVIL WAR
        elif card['id'] == 40:
            for p in ["Russia", "China","EU", "US"]:
                utils.setInfluence(self, "Somalia", p, 0, logger)
            utils.addInfluence(self, "Somalia", player, 1, logger)
            
            somalia=utils.getCountry(self, "Somalia")
            somalia["adjacent"].append("Saudi Arabia")
            response=requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Somalia', json=somalia)
            
            sarabia=utils.getCountry(self, "Saudi Arabia")
            sarabia["adjacent"].append("Somalia")
            response=requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/Saudi Arabia', json=sarabia)
            logger.info(f"RESPONSE IS {response.json()}")
           
            
            
        #SOUTH LEBANON CONFLICT
        elif card['id'] == 41:
            utils.setInfluence(self, "Lebanon", "US", 1,logger)
            
            #Country specifics
            country=utils.getCountry(self, "Lebanon")
            country["comments"]='{"no edge":["EU", "Russia", "China"], "no loss": ["US"]}'
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
        #SUDAN CIVIL WARS
        elif card['id'] == 42:
            # Roll a dice
            diceRoll = utils.roll()

            if logger!=None: logger.info(f"Roll {diceRoll}")
            # Get what we have to add
            
            for country in utils.getCountry(self, "Sudan")["adjacent"]:
                if logger!=None: logger.info(f"\tCountry: {country}")
                we=utils.whoEdges(self, country, logger)
                if(we in self.ifactions[self.factions[player]]):
                    diceRoll+=1
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] <= 4:
                #pre
                if(self.factions[player]=="W"):
                    diceRoll+=1
            else:
                if(self.factions[player]=="E"):
                    diceRoll+=1
            
            # If modified dice throw in 4-6
            logger.debug(f'Modified dice throw: {diceRoll}')
            if diceRoll > 3:
                logger.info("Removing influence for other powers")
                for power in body["players"]:
                    utils.addInfluence(self, "Sudan", player, -1)
                logger.info("Adding influence country")
                utils.addInfluence(self, "Sudan", player, 1)
        
        #TIANANMEN PROTESTS
        elif card['id'] == 43:
            logger.info("TIANANMEN PROTESTS")
            self.increment_player_score("China", -2)
            utils.setInfluence(self, "China", "US", 0, logger)
            utils.setInfluence(self, "China", "EU", 0, logger)
            utils.setInfluence(self, "China", "Russia", 0, logger)
            utils.addInfluence(self, "China", "China", 1, logger)
            
        #UNCOMFORTABLE DEMOCRACIES
        elif card['id'] == 44:
            self.increment_player_score(player, 1)
            options=["Venezuela", "Ecuador", "Bolivia", "Brazil", "Argentina"]
            options2=["Israel", "Ukraine"]
            if("operation" in body.keys() and "targets" in body.keys()):
               if logger!=None: logger.info("Conditions met")
               if(body["operation"]=="remove" and "players" in body.keys()):
                  if logger!=None: logger.info("Remove")
                  if(len(body["targets"])<2 and len(body["targets"])==len(body["players"])):
                      if logger!=None: logger.info("\tRemove conditions met")
                      for i in range(len(body["targets"])):   
                        if(body["targets"][i] in options2):                                            
                          utils.addInfluence(self, body["targets"][i], body["players"][i], -2)
                  else:
                      return False #maximum 2 targets
               elif(body["operation"]=="add" and len(body["targets"])==1 and body["targets"][0] in options):
                   if logger!=None: logger.info("\Add conditions met")
                   utils.addInfluence(self, body["targets"][0], player, 1, logger)
               else:
                    return False #
            else:
                return False #body must contain operation and targets
        
        #WOLFWOVITZ DOCTRINE
        elif card['id'] == 45:
            if("targets" in body.keys() and "players" in body.keys()):
                  logger.info("1st contition met")
                  if(len(body["targets"])<=2 and len(body["targets"])==len(body["players"])):
                      logger.info("2nd contition met")
                      for i in range(len(body["targets"])):   
                        country=utils.getCountry(self, body["targets"][i])
                        logger.info(f"Country {country}")
                        if(country["isOilProducer"] or country["isConflictive"]):                                            
                          utils.addInfluence(self, body["targets"][i], body["players"][i], -1, logger)
                  else:
                      return False #maximum 2 targets
            else:
                return False #body must contain operation and targets
            self.increment_player_score("US", -1)
       
       #YUGOSLAV WARS
        elif card['id'] == 46:
            logger.info("Increment score")
            self.increment_player_score("EU", -1)
            logger.info("Edge the balkans")
            utils.edgeCountry(self,"Balkan States", "EU", logger)
        
        #9/11 ATTACKS
        elif card['id'] == 47:
            logger.info("9/11 attacks")
            if(utils.whoEdges(self,"United States",logger)=="US"):
                logger.info("Adding influence to US")
                utils.addInfluence(self, "United States", "US", 2)
                logger.info(f"Adding influence to EU: {body['targets']}")
                if(len(body["targets"])==2 and len(body["targets"])==len(set(body["targets"]))):
                    for i in range(len(body["targets"])):  
                        target=body["targets"][i]
                        logger.info(f"Adding influence to {target}")
                        if(target in self.UEmembers):
                            utils.addInfluence(self, target, "US", 1,logger)
                        else:
                            logger.info("ERROR: 9/11 ATTACKS: No EU member")
            else:
                utils.edgeCountry(self, "United States", "US", logger)
            self.increment_player_score("US", -2)
        
        #ABM TREATY WITHDRAWAL
        elif card['id'] == 48:
            self.increment_player_score("US", -3)
            self.increment_player_score("China", -1)
            self.increment_player_score("Russia", -1)
            #TODO: EAST BLOCK IF 2 PLAYERS
        
        #ABU GRAHIB
        elif card['id'] == 49:
            self.increment_player_score("US", -2)
            
        #AFRICA
        elif card['id'] == 50:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
        
        #AFRICAN UNION
        elif card['id'] == 51:
            if(len(body["targets"])==1):
                country=utils.getCountry(self, body["targets"][0])
                if(country["region"]=="Africa" and country["name"]!="Morocco"):
                    if(len(body["players"])==1 and self.factions[body["players"][0]]=="W"):
                        utils.addInfluence(self, body["targets"][0], body["players"][0], -1)
            #TODO: constrains to influence
            
        #AL QAEDA
        elif card['id'] == 52:
            logger.debug("TODO")
        
        #ALBA
        elif card['id'] == 53:
            options=['Venezuela', 'Ecuador', 'Bolivia', 'Cuba', 'Honduras']
            if("targets" in body.keys()):
                if(len(body["targets"])<=2 and len(body["targets"])==len(set(body["targets"]))):
                    for t in body["targets"]:
                        country=utils.getCountry(self, t)
                        if(country in options):
                            utils.addInfluence(self, t, "US", -1)
        
        #ARAB SPRING
        elif card['id'] == 54:
            options=['Egypt', 'Tunisia']
            options2=['Morocco', 'Saudi Arabia', 'Gulf States']
            if("targets" in body.keys()):
                if(len(body["targets"])==1 and body["targets"][0] in options):
                    utils.setInfluence(self, body["targets"][0], "US", 0)
                    utils.setInfluence(self, body["targets"][0], "EU", 0)
                elif("players" in body.keys() and len(body["targets"])==len(body["players"])):
                    for i in range(len(body["targets"])):
                        if(body["targets"][i] in options2):
                            utils.addInfluence(self, body["targets"][i], body["players"][i], -1)
          
        #ASIA
        elif card['id'] == 55:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
        
        #AUSTERITY PLANS
        elif card['id'] == 56:
            self.increment_player_score("EU", -2)
            contUS=0
            contEU=0
            if("targets" in body.keys() and "players" in body.keys()):
                if(len(body["targets"])<=3 and len(body["targets"])==len(body["players"])):
                    for i in range(len(body["targets"])):
                        if(body["players"]=="US"):
                            contUS+=1
                        elif(body["players"]=="EU"):
                            contEU+=1
                        elif(contEU>2 or contUS>1):
                            return False
                        utils.addInfluence(self, body["targets"][i], body["players"][i], 1)
           
        #BRICS
        elif card['id'] == 57:
            brics=['Brazil', 'Russia', 'India', 'China', 'South Africa']
            for bric in brics:
                logger.info(f"{bric}")
                p=utils.whoEdges(self, bric, logger)
                logger.info(f"{bric} edged by {p}")
                if(p!=""):
                    self.increment_player_score(p, 1)
            for p in ["US", "EU", "China", "Russia"]:
                self.increment_player_score(p, -2)
    
        #CENTRAL-NORTH AMERICA
        elif card['id'] == 58:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
        
        #CLIMATE CHANGE
        elif card['id'] == 59:
            for p in ["US", "EU", "China", "Russia"]:
                self.increment_player_score(p, -1)
            board = self.board_map_get()
            for k in board["nwo"]["Economy"].keys():
                p=board["nwo"]["Economy"][k]["supremacy"]
                if(p!="" and p!=None):
                    self.increment_player_score(p, -1)
            for k in board["nwo"]["Technology"].keys():
                p=board["nwo"]["Technology"][k]["supremacy"]
                if(p!="" and p!=None):
                    self.increment_player_score(p, -1)
                    
        #COLOR REVOLUTION        
        elif card['id'] == 60:
            options=['Caucasus States', 'Ukraine', 'Balkan States', 'Stan States']
            if("targets" in body.keys() and len(body["targets"])==1):
               if(body["targets"][0] in options):
                   utils.setInfluence(self, body["targets"][0], "Russia", 0)
        
        #EASTERN ADHESION
        elif card['id'] == 61:
            self.increment_player_score("EU", 1)
            adhesion=["Hungary", "Poland"]
            for k in adhesion:
                self.UEmembers.append(k)
            
            if(len(body["targets"])==1 and body["targets"][0] in adhesion):
                utils.addInfluence(self, body["targets"][0], player, 1)
        
        #ECONOMIC RESCUE
        elif card['id'] == 62:
            options=['South Korea', 'Indonesia', 'Thailand', 'Philippines', 'Greece', 'Italy', 'Spain-Portugal']
            if("targets" in body.keys() and len(body["targets"])==1):
               logger.info("Targets ok")
               country=utils.getCountry(self, body["targets"][0])
               if(body["targets"][0] in options or country["region"]=="South America"):
                   logger.info("\tTarget ok") 
                   utils.setInfluence(self, body["targets"][0], player, 2, logger)
               else:
                   logger.info("ERROR: ECONOMIC RESCUE - no valid target")
        #FOIA
        elif card['id'] == 63:
            self.increment_player_score(player, 1)
            #TODO: open hand
        
        #FUCK THE EU
        elif card['id'] == 64:
            options=['Benelux', 'France', 'Germany', 'Italy']
            if("targets" in body.keys() and len(body["targets"])==1):
               if(body["targets"][0] in options):
                   utils.addInfluence(self, body["targets"][0], "US", -1)
            utils.addInfluence(self, "Ukraine", "US", 1)
    
        #GLOBALIZATION    
        elif card['id'] == 65:
            logger.info(f"{len(body['targets'])}, {len(body['players'])}")
            if(len(body["targets"])==5 and len(body["players"])==5):
                for i in range(len(body["targets"])):
                    logger.info(f" \t{i}")
                    utils.addInfluence(self, body["targets"][i], body["players"][i], 1)
            else:
                logger.debug("ERROR: GLOBALIZATION: must be 5 targets")
        
        #GUANTANAMO
        elif card['id'] == 66:
            self.increment_player_score("US", -1)
            #Ongoing effect reflected by being in play and in frontend
            
        #HEZBOLLAH
        elif card['id'] == 67:
            logger.debug("TODO")
        
        #HU JINTAO
        elif card['id'] == 68:
            if(len(body["targets"])>=2):
                add=True
                points=1
                for i in range(2): #countries to remove
                    name=body["targets"][i]
                    country=utils.getCountry(self, name)
                    ec=utils.whoEdges(self, name, logger)
                    if(ec=="China"):
                        points+=utils.removeEdge(self, body["targets"][i], "China", logger)
                    else:
                        add=False
                        logger.info("ERROR: HU JINTAO: No edge from China in country")
                        break
                    logger.info(f"points at: {points}")
                    
            if(add):
                for i in range(2): #countries to remove
                    utils.removeEdge(self, body["targets"][i], "China")
                cadd=body["targets"][2:]
                if(len(cadd)==len(set(cadd))):#countries to add
                    for i in range(2,points):
                        name=body["targets"][i]
                        country=utils.getCountry(self, name)
                        if(country["region"] in ["Asia", "Africa", "South Ameria", "North-Central America"] and not country["name"] in ["US", "Russia"]):
                            utils.addInfluence(self, name, "China", 1)
                        else:
                            logger.info("ERROR: HU JINTAO: Invalid country for influence")
                else:
                    logger.info("ERROR: HU JIN")
                    
                    
        #HUGO CHAVEZ
        elif card['id'] == 69:
            if(len(body["players"])==1):
                if(self.factions[body["players"][0]]=="W"):
                    utils.addInfluence(self, "Venezuela", body["players"][0], -1)
                else:
                    logger.info("ERROR: HUGO CHAVEZ: not W target")
            else:
                logger.info("ERROR: HUGO CHAVEZ: not a single target")
        
            utils.addInfluence(self, "Venezuela", player, 1)
            
            country=utils.getCountry(self, "Venezuela")
            country["comments"]='{"no influence":["US"]}'
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
            
            
            
        #INVASION OF AFGHANISTAN
        elif card['id'] == 70:
            removed=requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/removed').json()
            logger.info(f"Removed cards: {removed}")
            if(not 47 in removed):
                self.increment_player_score("US", -1)
                
            utils.addInfluence(self, "Afghanistan", "US", 1)
            utils.addInfluence(self, "Pakistan", "US", 1)
            
        #INVASION OF CRIMEA
        elif card['id'] == 71:
            utils.addInfluence(self, "Ukraine", "Russia", 1)
            self.increment_player_score("Russia", -1)
            logger.info("VP and Russian influence changed")
            utils.removeEdge(self, "Ukraine", "US",logger)
            utils.removeEdge(self, "Ukraine", "EU",logger)
            
        #IRAQ WAR
        elif card['id'] == 72:
            self.increment_player_score("US", -1)
            utils.edgeCountry(self, "Iraq", "US", logger)
            
        #JULIAN ASSANGE   
        elif card['id'] == 73:
            self.increment_player_score("US", -3)
            self.increment_player_score("EU", -1)
            self.increment_player_score("Russia", -1)
            self.increment_player_score("China", -1)
        
        #KIM JONG IL
        elif card['id'] == 74:
            utils.setInfluence(self, "North Korea", "EU", 0)
            utils.setInfluence(self, "North Korea", "US", 0)
            utils.addInfluence(self, "North Korea", player, 1)
          
            country=utils.getCountry(self, "North Korea")
            country["comments"]='{"no influence":["EU", "US"], "no destabilization": ["US", "EU"]}'
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        
        #KYOTO PROTOCOL (DONE) - TODO: not sure if it's updating it
        elif card['id'] == 75:
            board = self.board_map_get()
            if("options" in body.keys() and len(body["options"])==len(body["players"])):
                logger.info("1st condition met")
                for i in range(len(body["options"])): #for each player
                    logger.info(f"Checking {i}:")
                    if body["players"][i] in self.players:
                        logger.info(f"Player is ok")
                        if body["options"][i]=="no":
                            logger.info("\t Chooses no")
                            self.increment_player_score(body["players"][i], -1)
                        elif body["options"][i]=="yes":
                            logger.info("Chooses yes")
                            if("targets" in body.keys()):
                                torem=body["targets"][i]
                                logger.info(f"\t\tChooses to remove {torem}")
                                track=None
                                if(torem in board["nwo"]["Economy"].keys()):
                                    nwoi=board["nwo"]["Economy"][torem]
                                    track="Economy"
                                elif(torem in board["nwo"]["Technology"].keys()):
                                    nwoi=board["nwo"]["Technology"][torem]
                                    track="Technology"
                                else:
                                    logger.info("No NWO Found")
                                    return False #no NWO found
                                logger.info(f"\t\tSupremacy on {torem}: {nwoi}")
                                if(nwoi["supremacy"]==body["players"][i]):
                                    nwoi["supremacy"]=""
                                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/{track}/{torem}', json=nwoi)
                              
                                else:
                                    logger.info("No supremacy on selection")
                                    return False #no supremacy on selection
                        else:
                            logger.info("No options in body")
                            return False #no "options" in body
            
        #LibyaN CIVIL WAR
        elif card['id'] == 76:
            country=utils.getCountry(self, "Libya")
            p=utils.whoEdges(self,"Libya", logger)
            logger.info(f"{p} is edging libya")
            self.increment_player_score(p, -1)
            for p in self.players:
                utils.setInfluence(self, country['name'], p, 0)
            logger.info('adding influence')
            utils.addInfluence(self, "Libya", player, 1)
        
            logger.info("removing oil producer and special effects")
            country["isOilProducer"]=False
            country["comments"]=""
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
           
            
        #NEW START
        elif card['id'] == 77:
            board = self.board_map_get()
            if("options" in body.keys() and len(body["options"])<=2):
                for k in body["options"]:
                    if k in ["Russia", "US"] and k in self.players:
                        if "targets" in body.keys() and len(body["targets"])==len(body["options"]):
                            if(body["options"][k]=="remove"):
                                torem=body["targets"][k][0]
                                track=None
                                if(torem in board["nwo"]["Economy"].keys()):
                                    nwoi=board["nwo"]["Economy"][torem]
                                    track="Economy"
                                elif(torem in board["nwo"]["Technology"].keys()):
                                    nwoi=board["nwo"]["Technology"][torem]
                                    track="Technology"
                                else:
                                    return False #no NWO found
                                if(nwoi["supremacy"]==k):
                                    nwoi["supremacy"]=""
                                    self.increment_player_score(k, 1)  
                                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/{track}/{torem}', json=nwoi)
                                else:
                                    return False #no supremacy on selection
            
        #NORD STREAM 1
        elif card['id'] == 78:
            #Ongoing effect on scoring (OPEC)
            if("targets" in body.keys()):
                if(body["targets"][0] in self.UEmembers and body["targets"][0]!="United Kingdom"):
                    utils.addInfluence(self, body["targets"][0], "Russia", 1)

        #NWO
        elif card['id'] == 79:
            if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] >= 6:
                self.increment_player_score(player, -2)
                
                #TODO: end game
                #game["isFinished"]=True #is this enough?
            else:
                return False #wrong round
        
        #PRISM
        elif card['id'] == 80:
            self.increment_player_score("US", -1)
            if("targets" in body.keys()):
                target=body["targets"][0]
                country=utils.getCountry(self, target)
                if("EU" in country["influence"].keys()):
                    utils.addInfluence(self, target, "US", -1)
                else:
                    logger.info("ERROR: CARD TEXT - PRISM: No influence from UE in target country")
        #SECOND EASTERN ADHESION
        elif card['id'] == 81:
            self.increment_player_score("EU", 1)
            adhesion=["Romania", "Bulgaria"]
            for k in adhesion:
                self.UEmembers.append(k)
            
            if(len(body["targets"])==1 and body["targets"][0] in adhesion):
                utils.addInfluence(self, body["targets"][0], player, 1)
        
        #SOUTH AMERICA
        elif card['id'] == 82:
            requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/playing/score/'+card["id"])
      
        #SYRIAN CIVIL WAR
        elif card['id'] == 83:
            country=utils.getCountry(self, "Syria")
            for k in country["influence"]:
                if k=="Russia":
                    utils.setInfluence(self, "Syria", k, 1)
                else:
                    utils.setInfluence(self, "Syria", k, 0)
            self.increment_player_score("Russia", -1)
            
        #THE KIRCHNERS
        elif card['id'] == 84:
            if("targets" in body.keys()):
                target=body["targets"][0]
                if target in ["Argentina", "Chile", "Uruguay", "Paraguay"]:
                    utils.addInfluence(self, target, player, 1)
            #Ongoing effects - when determining influence targets
        
        #THE MOTHER OF ALL WARS
        elif card['id'] == 85:
            #Launch fist call
            logger.info("THE MOTHER OF THE LAMB")
            ret=self.cards_play_destabilization(player, id, body={"target":body["targets"][0], "targets":body["players"]}, validate=False, wrap=True)
            logger.info(f"RETURNING {ret}")
            return ret #returns the dice roll result (no need for wrapping, is was either done if unsuccessful, it will be done on second call if successful)
            
        #VIKTOR YUSHCHENKO
        elif card['id'] == 86:
            self.increment_player_score("Russia", -1)
            utils.addInfluence(self, "Ukraine", "Russia", -1)
    
        #VLADIMIR PUTIN    
        elif card['id'] == 87:
            utils.addInfluence(self, "Russia", "Russia", 1)
            inplay=requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
            logger.info(f"Cards in play: {inplay}")
            if(15 in inplay):
                utils.addInfluence(self, "Russia", "Russia", 1)
            #TODO: ongoing effect
            
        #WAR ON TERROR
        elif card['id'] == 88:
            #Ongoing effect on destabilization
            pass
        
        else:
            return False #card id not found
        
        if(wrap): #always except on some rare cases (playing cards from discard)
            # Handle the player's played card
            self.handle_players_card(player, card)
    
            # Handle the player's play
            self.handle_players_play(player)

        return True
    
    def cards_play_score(self, player, id, body, validate=False, logger=None):
        # If not the player's turn
        if self.is_players_turn(player) == False: 
            if(logger!=None): logger.info("ERROR SCORE: No player's turn")
            return False

        # Check if the card exists
        card = self.card_get(id)
        if card == {}: 
            if(logger!=None): logger.info("ERROR SCORE: Nonexisting card")
            return False
        
        # It has to be a punctuation card
        if card['type'] != 'Punctuation': 
            if(logger!=None): logger.info("ERROR SCORE: It is not an scoring card")
            return False

        # Get the board
        board = self.board_map_get()
        if(logger!=None): logger.info(f"\n{player} SCORING {id}: {card['title']}\n")
        if(id==31): #OPEC, does not go as the rest
            if(logger!=None): logger.info("SCORE: OPEC")
            countries = [country for country in board['countries'] if country['isOilProducer']]
            maxPlayers=[]
            maxOil=0
            inplay=requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
            
            for eachPlayer in self.playingOrder:
                #oilProducersEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country) and country['isOilProducer']]
                oilProducersEdged = []
                for country in countries:
                    if utils.whoEdges(self, country["name"])==eachPlayer: 
                        oilProducersEdged.append(country)
                
                #NordStream
                if eachPlayer=="EU" and 78 in inplay and not "Russia" in oilProducersEdged:
                    oilProducersEdged.append("Russia")
                
                if len(oilProducersEdged)>maxOil:
                    maxOil=len(oilProducersEdged)
                    maxPlayers=[]
                    maxPlayers.append(eachPlayer)
                elif len(oilProducersEdged)==maxOil:
                    maxPlayers.append(eachPlayer)
                
                logger.info(f"SCORE OPEC {eachPlayer} {len(oilProducersEdged)}-2")
                self.increment_player_score(eachPlayer, len(oilProducersEdged))
                self.increment_player_score(eachPlayer, -2)
                if requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/round').json()['round'] > 4:
                    logger.info(f"SCORE OPEC {eachPlayer} {len(oilProducersEdged)}-2")
                    self.increment_player_score(eachPlayer, len(oilProducersEdged))
                    self.increment_player_score(eachPlayer, -2)
            
            #Oil Crisis
            if(29 in inplay): 
                for p in self.playingOrder:
                    if(p in maxPlayers):
                        self.increment_player_score(p, 1)
                    else:
                        self.increment_player_score(p, -1)
                
                #Remove from inplay to discard
                requests.delete(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing/29')
                requests.post(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/deck/discarded/29')
                
                    
                    
                
        else:
            # The region has to exist
            if body['region'] not in board['regions']: 
                if(logger!=None): logger.info(f"ERROR SCORE: Region {body['region']} does not exist in {board['regions']}")
                return False
    
            # If only validate, return here
            if validate == True: return True
            
            # Get the countries of the specified region
            if(logger!=None): logger.info("SCORE: Getting countries...")
            
            countries = [country for country in board['countries'] if body["region"] in country['region']]
            
            if(logger!=None): logger.info("SCORE: Evaluating presence...")
            #
            # Evaluate presence-----------------------------------------------
            for eachPlayer in self.playingOrder:
                countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]
                if len(countriesEdged) > 0:
                    logger.info(f"PRESENCE: {eachPlayer} +{board['regionScoring'][body['region']]['presence']}")
                    self.increment_player_score(eachPlayer, board['regionScoring'][body['region']]['presence'])
    
            if(logger!=None): logger.info("SCORE: Evaluating domination...")
            #
            # Evaluate domination---------------------------------------------
            domination = {}
            for eachPlayer in self.playingOrder:
                if(logger!=None): logger.info(f"\tSCORE: {eachPlayer}")
                countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]
                
                conflictive = False
                nonConflictive = False
    
                for country in countriesEdged:
                    if country['isConflictive']: conflictive = True
                    if not country['isConflictive']: nonConflictive = True
                
                if(logger!=None): logger.info(f"\tSCORE: Number of countriesEdged {len(countriesEdged)}")
                
                # Store the number of countries that the player has the edge in and if at least one country is conflictive and at least another one is not, from within the countries that he has the edge in
                domination[eachPlayer] = {'count': len(countriesEdged), 'domination': False}
                
                if conflictive and nonConflictive: 
                    domination[eachPlayer]['domination']=True
    
            if(logger!=None): logger.info("SCORE: Evaluating domination player...")
    
            # If there is a player with more countries edged than any other
            points = [domination[player]['count'] for player in domination]
            if points.count(max(points)) == 1:
                
                for key, val in domination.items():
                    logger.info(f"DOMINATION {key} {val}")
                    # Find the player more countries edged than any other
                    if val['count'] == max(points):
                        
                        if val['domination'] == True:
                            logger.info(f"DOMINATION: {key} +{board['regionScoring'][body['region']]['domination']}")
                            self.increment_player_score(key, board['regionScoring'][body['region']]['domination'])
    
            if(logger!=None): logger.info("SCORE: Evaluating control...")
    
            #
            # Evaluate control-------------------------------------------------
            control = {}
            for eachPlayer in self.playingOrder:
                if(logger!=None): logger.info(f"SCORE: {eachPlayer}")
                countriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country)]
    
                nonConflictive = False
    
                for country in countriesEdged:
                    if not country['isConflictive']: 
                        nonConflictive = True
                
                # Store the number of countries that the player has the edge in and if at least one country is non conflictive, from within the countries that he has the edge in
                control[player] = {'count': len(countriesEdged), 'control': False}
                if conflictive and nonConflictive: 
                    control[player]['control']= True
    
            if(logger!=None): logger.info("SCORE: CONTROL: Evaluating more edged countries")
            # If there is a player with more countries edged than any other
            points = [control[player]['count'] for player in control]
            if points.count(max(points)) == 1:
                
                for key, val in control.items():
                    
                    # Find the player more countries edged than any other
                    if val['count'] == max(points):
                        
                        # If player has edge in non conflictive country and also has edge in all confilctive countries
                        if val['control'] == True and val['count'] >= len([country for country in countries if country['isConflictive']]):
                            logger.info(f"CONTROL: {key} +{board['regionScoring'][body['region']]['presence']}")
                            self.increment_player_score(key, board['regionScoring'][body['region']]['control'])
    
            if(logger!=None): logger.info("SCORE: Evaluating conflictive countries...")
        
            #
            # Evaluate conflictive countries-----------------------------------
            for eachPlayer in self.playingOrder:
                conflictiveCountriesEdged = [country for country in countries if self.is_player_with_edge(eachPlayer, country) and country['isConflictive']]
                if(len(conflictiveCountriesEdged)>0):
                    self.increment_player_score(eachPlayer, len(conflictiveCountriesEdged))
                    logger.info(f"CONFLICTIVE: {eachPlayer} +{len(conflictiveCountriesEdged)}")
                
            if(logger!=None): logger.info("SCORE: Evaluating superpower adjacency...")
    
            # Evaluate superpower adjacency -----------------------------------
            # TODO: this is givin 500 and is not well done, must be countries IN the scored region
            # Evaluate countries edged by another players that are adjacent to the player's superpower countries. The player also loses 1 VP per each of his superpower countries edged by another player
            supercountries={'US': ['United States'], 'EU': self.UEmembers, 'China': ['China'], 'Russia': ['Russia']}
            pointsToLose={"US":set(), "EU":set(), "Russia":set(), "China":set()}
            for country in countries: #for each country in the region
                for superpower in supercountries:
                    logger.info(f"{superpower}")
                    for supercountry in supercountries[superpower]:
                        logger.info(f"{supercountry}")
                        if(country["name"]==supercountry or supercountry in country["adjacent"]):
                            logger.info("Checking edge...")
                            ec=utils.whoEdges(self, country["name"])
                            if(ec!="" and ec!=superpower):
                                logger.info("Country to lose")
                                pointsToLose[superpower].add(country["name"])
            for p in self.players:
                     self.increment_player_score(key, -len(pointsToLose[p]))
                     logger.info(f"ADJACENT: {p} {-len(pointsToLose[p])}")
                
                                
            # for key, val in {'US': ['United States'], 'EU': self.UEmembers, 'China': ['China'], 'Russia': ['Russia']}.items():
            #     #if(logger!=None): logger.info(f"SCORE: Evaluating {key} superpower adjacency {val}...")
                
            #     #if(logger!=None): logger.info(f"SCORE: Evaluating supercountries edged by others...")
            #     pointsToLose=0
            #     for c in val:
            #         if(logger!=None): logger.info(f"SCORE: Evaluating supercountry {c}...")
            #         supercountry=utils.getCountry(self, c)
            #         if(logger!=None): logger.info(f"SCORE: Evaluating supercountry {supercountry}...")
            #         if(logger!=None): logger.info(f"SCORE: \tRegion is {body['region']}")
                    
            #         if(supercountry["region"]==body["region"]):
            #             if(logger!=None): logger.info(f"SCORE: \tChecking whoedges")
            #             ec=utils.whoEdges(self,c,logger)
            #             if(logger!=None): logger.info(f"SCORE: \tEdges: {ec}")
            #             if(ec!="" and ec!=key):
            #                 pointsToLose-=1
                
            #     #if(logger!=None): logger.info(f"SCORE: Evaluating countries in region adjacent to supercountries and edged by others...")
            #     pointsToLose = -len([country for country in countries if self.is_another_player_with_edge(key, country) and any(c in country['adjacent'] for c in val)])
            #     if pointsToLose != 0:
            #         self.increment_player_score(key, pointsToLose)
            #         logger.info(f"ADJACENT: {eachPlayer} {pointsToLose}")
             
        if(logger!=None): logger.info("SCORE: Wraping up...")
        
        #
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        
        return True

    #deal with a card that is cancelled
    def cards_play_cancel(self, player, id, validate=False, logger=None):
        # If not the player's turn
        if self.is_players_turn(player) == False: 
            if(logger!=None): logger.info("Not player's turn")
            return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}: 
            if(logger!=None): logger.info("Card does not exist")
            return False

        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        return True

    def cards_play_nwo(self, player, id, body, validate=False):
        # If not the player's turn
        if self.is_players_turn(player) == False: return False
        
        # Check if the card exists
        card = self.card_get(id)
        if card == {}: return False

        # Get the board
        board = self.board_map_get()

        # The nwo track slot has to exist
        slotsNames = []
        [slotsNames.extend(list(slot.keys())) for slot in list(board['nwo'].values())]
        if body['name'] not in slotsNames: return False

        # Find the track and the slot
        for track in board['nwo']:
            for slot in board['nwo'][track]:
                
                if slot == body['name']:
                    
                    # Check if there is a veto against this player or if there is another player in the ahead field
                    if board['nwo'][track][slot]['veto'] == player or board['nwo'][track][slot]['ahead'] in [anotherPlayer for anotherPlayer in self.playingOrder if anotherPlayer != player]:
                        return False

                    # If only validate, return here
                    if validate == True: return True

                    # Remove the veto and the ahead from the nwo track slot
                    board['nwo'][track][slot]['veto'] = board['nwo'][track][slot]['ahead'] = ''

                    # If there was supremacy, remove it, otherwise, give it to the player
                    if board['nwo'][track][slot]['supremacy'] != '':
                        board['nwo'][track][slot]['supremacy'] = ''
                    else:
                        board['nwo'][track][slot]['supremacy'] = player

                    # Update the track slot
                    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/{track}/{slot}', json=board['nwo'][track][slot])

        #
        # Handle the player's played card
        self.handle_players_card(player, card)

        # Handle the player's play
        self.handle_players_play(player)
        
        return True
