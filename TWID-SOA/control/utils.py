#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 11:43:25 2023

@author: rodri
"""
import random
import requests
import config
import validators
from pydantic import BaseModel, ValidationError, validator


modifiers={}
def roll(d=6):
    return random.randint(1,6)

def getOpsModifiers(self, card, player, operation, use=[]): 
    import json 
    
    mods=0
    #NWO mods
    nwo=self.board_map_get()["nwo"]
    
    if(card["type"]=="Military" or ("subtype" in card.keys() and card["subtype"]=="Military")):
        if(nwo["Technology"]["Communications"]["supremacy"]==player):
            mods+=1
    if(operation=="influence"):
        if(nwo["Public opinion"]["Mass media"]["supremacy"]==player):
            mods+=1
    
    if(card["type"]=="Economy" or ("subtype" in card.keys() and card["subtype"]=="Economy")):
        if(nwo["Economy"]["Financial markets"]["supremacy"]==player):
            mods+=1
        if(nwo["Economy"]["Sovereign funds"]["supremacy"]==player):
            if("Sovereing funds" in use): 
                mods+=2
                nwo["Economy"]["Sovereign funds"]["supremacy"]=""
                requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Economy/Sovereign funds', json=json.dumps(nwo["Economy"]["Sovereign funds"]))
    if(nwo["Public opinion"]["Information leaks"]["supremacy"]!=player and nwo["Public opinion"]["Information leaks"]["supremacy"]!=""):
        if("Information leaks" in use): 
            mods-=2
            nwo["Public opinion"]["Information leaks"]["supremacy"]=""
            requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/nwo/Public opinion/Information leaks', json=json.dumps(nwo["Economy"]["Sovereign funds"]))
          
    #In play mods
    inplay=self.cards_playing_get()
    print(f"Cards in play: {inplay}")
    #anti-globalization
    if(2 in inplay and (card["type"]=="Economy" or ("subtype" in card.keys() and card["subtype"]=="Economy"))):
        mods-=1
    #g20
    #TODO: have the g20 in mind in the frontend
    if(16 in inplay and player in self.g20):
        mods+=self.g20[player]
        if(len(self.players)==4):
            self.g20[player]-=1
    print(f"Total modifiers: {mods}")
    return mods

def modify(order, value):
    if not order in modifiers.keys():
        modifiers[order]=value
    else:
        modifiers[order]+=value

def getCountry(self, name):
    #country = requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{name}').json()
    #return country
    countries = self.board_map_get()['countries']
    country = [eachCountry for eachCountry in countries if eachCountry['name'] == name]
    if len(country) < 1: return False
    else: return country[0]

#EDGE UTILS
#Adds enough influence to edge country   
def edgeCountry(self, name, player, logger=None):
    if(logger!=None): logger.info(f"Edging {name} for {player}")
    country=getCountry(self,name)
    if(logger!=None): logger.info(f"Edging {country}")
    
    if len(country["influence"])==0 or not player in country['influence'].keys():
        country["influence"][player]={"influence":0, "extra":{}}
        
    if(logger!=None): logger.info(f"Proceeding to edge")
    infs=[x["influence"] for x in country["influence"].values()]
    if(logger!=None): logger.info(f"Influences on country: {infs}")
    
    if(logger!=None): logger.info(f"Edging {country}")
    if(country["influence"][player]["influence"]<=max(infs)):
        if(logger!=None): logger.info(f"Proceeding to edge for sure")
        country["influence"][player]["influence"]=max(infs)+1
    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{name}', json=country)
    if logger!=None:         logger.info("PUT DONE")

#Deletes enough influence to lose edge in country
def removeEdge(self, name, player,logger=None):
    if logger!=None: logger.info(f"Removing edge from {name} for {player}")
    country=getCountry(self,name)
    ec=whoEdges(self,name, logger)
    if logger!=None: logger.info(f"Edged by {ec}")
    points=0
    while(ec==player):
        if logger!=None: logger.info(f"Reducing influence")
        country["influence"][player]["influence"]-=1
        points+=1
        requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{country["name"]}', json=country)
        ec=whoEdges(self,name, logger)
    if logger!=None: 
        logger.info("PUT DONE")
    return points #returns the number of points removed

def whoEdges(self, name, logger=None):
    val=0
    ce=""
    if logger!=None: logger.info(f"getting country {name}")
    country=getCountry(self,name)
    if logger!=None: logger.info(f"WHOEDGES {country}?")
    for k in country["influence"].keys():
        if logger!=None: logger.info(f"{k} with influence {country['influence'][k]['influence']}")
        if(country["influence"][k]["influence"]==val):
            ce=""
        elif(country["influence"][k]["influence"]>val):
            val=country["influence"][k]["influence"]
            ce=k
        if logger!=None: logger.info(f"{ce}")
    if logger!=None: logger.info(f"{country} edged by {ce}")  
    return ce
    
def isAdjacentOrWithInfluence(self, targetObject, player, logger=None):
    logger.info("isAdjacentorInfluence?")
    isCountryAdjacentOrWithInfluence = False
    if player not in targetObject['influence']:
        # If no influence in this country, check the adjacent countries
        logger.info("No influence")
        for eachCountry in targetObject['adjacent']:
            logger.info(eachCountry)
            country = getCountry(self, eachCountry)
            logger.info(country)
            if player in country['influence'] and country['influence'][player]['influence'] > 0:
                isCountryAdjacentOrWithInfluence = True
    else:
        isCountryAdjacentOrWithInfluence = True
        
    #Check the kirchners
    inplay=requests.get(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/cards/playing').json()
    if(84 in inplay and targetObject["name"] in ["Argentina", "Uruguay", "Chile", "Paraguay"] and player in ["Russia", "China"]):
        return True
    return isCountryAdjacentOrWithInfluence

def addInfluence(self, name, player, value, logger=None):
    if logger!=None: 
        logger.info(f"ADD INFLUENCE to {name} for {player}: {value}")
    country=getCountry(self,name)
    if logger!=None: 
        logger.info(f'country {country}')
    
    if not player in country['influence'].keys():
        country['influence'][player] = {'influence': value, 'extra': {}}
    else:
        country['influence'][player]["influence"]+=value
    if country['influence'][player]["influence"]<0:
        country['influence'][player]["influence"]=0
    if logger!=None: 
        logger.info(f"INFLUENCE ADDED {country}")
    
    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{name}', json=country)
    if logger!=None: 
        logger.info("PUT DONE")
 
def setInfluence(self, name, player, value, logger=None):
    if logger!=None: logger.info(f"SET INFLUENCE")
    if logger!=None: logger.info(f"Set influence {player} in {name} to {value}")
    country=getCountry(self,name)
    if logger!=None: logger.info(f"\t{country}")
    if not player in country['influence'].keys():
        if logger!=None: logger.info(f"\tIt had no previous influence")
        country['influence'][player] = {'influence': value, 'extra': {}}
    else:
        if logger!=None: logger.info(f"\tModifying prev influence")
        country['influence'][player]["influence"]=value
        
    if logger!=None: logger.info(f"\tChekcing if influence went neg")
    if country['influence'][player]["influence"]<0:
        country['influence'][player]["influence"]=0
    if logger!=None: logger.info("sending changes to board")
    requests.put(f'http://{config.ENV_URL_SERVICE_RESOURCES}/game/{self.id}/board/map/{name}', json=country)
    if logger!=None: logger.info("ending SET INFLUENCE")
    