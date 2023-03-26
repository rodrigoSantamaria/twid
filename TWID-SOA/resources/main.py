import json
from random import shuffle
from copy import deepcopy
from board import Board
from cards import Cards
from game import Game
import logging
import validators

# https://fastapi.tiangolo.com/advanced/response-change-status-code/
from fastapi import FastAPI, Response, status
app = FastAPI()

logger = logging.getLogger('resources_logger')
level=logging.DEBUG
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Custom OpenAPI 3.0 specification file
def custom_openapi():
    with open('openapi.json', 'r') as file:
        app.openapi_schema = json.load(file)
        return app.openapi_schema


# Definitions
app.openapi = custom_openapi
games = {}
board = None
cards = None


# Game endpoints
@app.get('/game')
async def game_get(response: Response):
    try:
        global games

        # If there are no games
        if games == []:
            response.status_code = status.HTTP_200_OK
            return []

        response.status_code = status.HTTP_200_OK
        return [{'id': gameId} for gameId in list(games.keys())]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game')
async def game_post(response: Response):
    try:
        global games
        # Idempotent
        game = Game()
        games[repr(game)] = game
        
        response.status_code = status.HTTP_200_OK
        return {'id':repr(game)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response.content=e
        return {'Error': e}


@app.delete('/game/{game}')
async def game_game_delete(game: str, response: Response):
    try:
        global games

        # Game must exist
        if game not in games:
            return {}
        
        # Remove it
        games.pop(game, None)

        response.status_code = status.HTTP_200_OK
        return {'id': game}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Board endpoints
@app.get('/game/{game}/board')
async def board_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        # Get the resources of the board
        board = games[game].board
        board = deepcopy(board.board)
        
        # Remove what we don't want
        board.pop('round', None)
        board.pop('score', None)
        board.pop('players', None)

        response.status_code = status.HTTP_200_OK
        return board
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/round')
async def board_round_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return {'round': board.round_get()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/board/round')
async def board_round_post(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # If success adding the round
        if board.round_add():
            response.status_code = status.HTTP_200_OK
            return {'round': board.round_get()}

        # If no success adding the round
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/board/round')
async def board_round_delete(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # Idempotent
        board.round_reset()

        response.status_code = status.HTTP_200_OK
        return {'round': board.round_get()}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/score')
async def board_score_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return board.score_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/score/{player}')
async def board_score_player_get(game: str, player: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return {'score': board.score_player_get(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/game/{game}/board/score/{player}')
async def board_score_player_put(game: str, player: str, body: validators.BodyBoardScorePlayer, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # If success updating the score
        if board.score_player_put(player, body.score):
            response.status_code = status.HTTP_200_OK
            return {'score': board.score_player_get(player)}

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/board/score/{player}')
async def board_score_player_delete(game: str, player: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # Idempotent
        board.score_player_put(player, 0)

        response.status_code = status.HTTP_200_OK
        return {'score': board.score_player_get(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/map')
async def board_map_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return board.map_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/map/{region}')
async def board_map_region_get(game: str, region: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return board.map_region_get(region)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/game/{game}/board/map/region/{region}')
async def board_map_region_put(game: str, region: str, body: validators.BodyBoardMapRegion, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # If success updating the score
        if board.map_region_put(region, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.map_region_get(region)

        # If no success updating the score
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/map/{region}/{country}')
#async def board_map_region_country_get(game: str, region: str, country: str, response: Response):
async def board_map_region_country_get(game: str, country: str, response: Response):
    logger.info("COUNTRY GET -------------------------------")
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        #return board.map_region_country_get(region, country)
        return board.map_country_get(country)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

@app.put('/game/{game}/board/map/{country}')
async def board_map_country_put(game: str, country: str, body: validators.BodyBoardMapRegionCountry, response: Response):
    logger.info("COUNTRY PUT -------------------------------")
    try:
        global games
        
        # If there is no game
        if game not in games.keys():
            logger.info("ERROR: game does not exist")
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board
        logger.info("UPDATING BOARD...")
        # If success updating the country
        if board.map_country_put(country, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            #return board.map_region_country_get(region, country)
            return board.map_country_get(country)

        # If no success updating the country
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/nwo')
async def board_nwo_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return [{'name': track} for track in board.nwo_get()]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/nwo/{track}')
async def board_nwo_track_get(game: str, track: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return [{'name': slot} for slot in board.nwo_track_get(track)]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_get(game: str, track: str, slot: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        response.status_code = status.HTTP_200_OK
        return board.nwo_track_slot_get(track, slot)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.put('/game/{game}/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_put(game: str, track: str, slot: str, body: validators.BodyBoardNwoTrackSlot, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # If success updating the track slot
        if board.nwo_track_slot_put(track, slot, json.loads(body.json())):
            response.status_code = status.HTTP_200_OK
            return board.nwo_track_slot_get(track, slot)

        # If no success updating the track slot
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/board/nwo/{track}/{slot}')
async def board_nwo_track_slot_delete(game: str, track: str, slot: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        board = games[game].board

        # Idempotent
        slotReset = board.nwo_track_slot_get(track, slot)
        slotReset['supremacy'] = ''
        board.nwo_track_slot_put(track, slot, slotReset)

        response.status_code = status.HTTP_200_OK
        return board.nwo_track_slot_get(track, slot)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Cards endpoints
@app.get('/game/{game}/cards')
async def cards_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return repr(cards)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/deck')
async def cards_deck_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return cards.cards_deck_get()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/deck/{type}')
async def cards_deck_type_get(game: str, type: str, response: Response, random: bool=False):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        deck = cards.cards_deck_get(type)
        if random == False: return [{'id': card} for card in deck]

        # If random is True, shuffle the deck
        shuffle(deck)
        return [{'id': card} for card in deck]

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}

#Add card to deck
@app.post('/game/{game}/cards/deck/{type}/{id}')
async def cards_deck_type_id_post(game: str, type: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success updating the deck with the new card
        if cards.cards_deck_add(type, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success updating the deck with the new card
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/cards/deck/{type}/{id}')
async def cards_deck_type_id_delete(game: str, type: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success deleting the card from the deck
        logger.info(f"DELETING CARD {id} from {type}")
        if cards.cards_deck_remove(type, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success deleting the card from the deck
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/playing')
async def cards_playing_get(game: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return [{'id': card} for card in cards.cards_playing_get()]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/playing/{id}')
async def cards_playing_post(game: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success adding the card to the playing cards
        if cards.cards_playing_add(id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success adding the card to the playing cards
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/cards/playing/{id}')
async def cards_playing_delete(game: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success removing the card from the playing cards
        if cards.cards_playing_remove(id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success removing the card from the playing cards
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# Has to be below the /cards/deck and /cards/playing as otherwise FastAPI wouldn't know if /cards/deck or /cards/playing or /cards/{id} was called
@app.get('/game/{game}/cards/{id}')
async def cards_id_get(game: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return cards.cards_get(id)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/player/{player}')
async def cards_player_player_get(game: str, player: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return [{'id': card} for card in cards.cards_player_get(player)]
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.get('/game/{game}/cards/player/{player}/header')
async def cards_player_player_header_get(game: str, player: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        response.status_code = status.HTTP_200_OK
        return {'id': cards.cards_player_header_get(player)}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/cards/player/{player}/header')
async def cards_player_player_header_delete(game: str, player: str, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success deleting the card as the player's header card
        id = cards.cards_player_header_unset(player)
        if id:
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success deleting the card as the player's header card
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


# These next 2 have to be below the /cards/player/{player}/header for the same reason as before
@app.post('/game/{game}/cards/player/{player}/{id}')
async def cards_player_player_id_post(game: str, player: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success adding the card to the player's hand
        if cards.cards_player_add(player, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success adding the card to the player's hand
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.delete('/game/{game}/cards/player/{player}/{id}')
async def cards_player_player_id_delete(game: str, player: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success deleting the card to the player's hand
        if cards.cards_player_remove(player, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success deleting the card to the player's hand
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}


@app.post('/game/{game}/cards/player/{player}/header/{id}')
async def cards_player_player_header_post(game: str, player: str, id: int, response: Response):
    try:
        global games

        # If there is no game
        if game not in games.keys():
            response.status_code = status.HTTP_200_OK
            return {}
        
        cards = games[game].cards

        # If success setting the card as the player's header card
        if cards.cards_player_header_set(player, id):
            response.status_code = status.HTTP_200_OK
            return cards.cards_get(id)

        # If no success setting the card as the player's header card
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {}
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {'Error': e}
