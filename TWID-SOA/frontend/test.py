#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File for testing the services

@author: rodri
"""
import requests
import time
import json
import random

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
os.chdir("/home/rodri/Documentos/docencia/tfms/javierVidal/TWID-SOA/frontend")
import validators
import utils

def getStatus(gameid, heads, options=["game", "boardmap", "round", "score", "cards"]):
    status={}
    if("game" in options):
        game = requests.get('https://localhost:443/game/'+gameid,verify=False)
        game=json.loads(game.content)
        status["game"]=game
        
    if("boardmap" in options):
        result = requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False)
        boardmap=json.loads(result.content)
        status["boardmap"]=boardmap
    #if debug: print(boardmap)
    
    if("round" in options):
        result = requests.get(f'https://localhost:443/game/{gameid}/board/round', verify=False)
        gameround=json.loads(result.content)
        status["round"]=gameround
    
    
    if("score" in options): 
        result = requests.get(f'https://localhost:443/game/{gameid}/board/score', verify=False)
        score=json.loads(result.content)
        status["score"]=score

    #1) Recoger cartas en mano
    if("cards" in options):
        cards={}
        headerCards={}
        for k in heads.keys():
            result = requests.get(f'https://localhost:443/game/{gameid}/cards/player', headers=heads[k], verify=False)
            cards[k]=json.loads(result.content)[k]["hand"]
            headerCards[k]=json.loads(result.content)[k]["header"]
        status["cards"]=cards
        status["headerCards"]=headerCards

    return status

################### ARRANCAR PARTIDA ####################
#1) Obtener tokens ----------------------------
debug=False
stats={"US":[], "Russia":[], "China":[], "EU":[]}
stats["scores"]={"Europe":[], "Asia":[], "OPEC":[],"Africa":[], "Middle East":[], "Central-North America":[], "South America":[]}
level="noob" #dummy-random, noob-basics, pro-let's see (complex)

t00=time.process_time()
for partida in range(100):
    for k in stats["scores"].keys():
        stats["scores"][k].append(0)
        
    if debug: print("----------------------- ARRANCAR PARTIDA -----------------------------")
    tokens={"US":"", "Russia":"", "EU": "", "China":""}
    for k in tokens.keys():
        if debug: print(k)
        result=requests.post("https://localhost:443/auth/signin/guest", verify=False)
        if debug: print(result.content)
        tokens[k]=eval(result.content)["access_token"]
    heads={}
    for k in tokens.keys():
        heads[k]={'X-ACCESS-TOKEN':"Bearer "+tokens[k]}
    #2) crear partida, obtenemos {game}
    game = requests.post('https://localhost:443/game', headers=heads["US"], verify=False)
    gameid=eval(game.content)["id"]
    
    
    #3) unirse a partida
    for k in tokens.keys():
        if debug: print(f'https://localhost:443/game/{gameid}/player/{k}')
        response = requests.post(f'https://localhost:443/game/{gameid}/player/{k}', headers=heads[k], verify=False)
        if debug: print(response)
    
    game = requests.get(f'https://localhost:443/game/{gameid}', headers=heads["US"], verify=False)
    if debug: print(game.content)
    
    #4) comenzar partida
    result = requests.post(f'https://localhost:443/game/{gameid}', headers=heads["US"], verify=False)
    
    if debug: print("Tiempo en arrancar la partida: ", time.process_time()-t00, "s")
    
    t01=time.process_time()
    status=getStatus(gameid, heads)
    if debug: print("Tiempo en obtener el status: ", time.process_time()-t01, "s")
    
    ###############################################################################
    """NOTA: Hasta aquí hemos iniciado una partida
    Ahora, por turnos, tenemos que jugar cartas de cabecera para establecer el orden
    Luego, se ejecutan cartas por orden
    """
    ###############################################################################
    usboost=[]
    for r in range(1,9):
        tr=time.process_time()
        if debug: print(f"----------------------- RONDA {r} -----------------------------")
        status=getStatus(gameid, heads)
        cards=status["cards"]
        
        if debug: print("----------------------- ELEGIR CABECERAS -----------------------------")
        #2) De momento cogemos simplemente la primera de la mano, por poner alguna, y luego ir probándolas
        for k in heads.keys():
            print(cards[k])
            headerid=utils.chooseCard(gameid,cards[k],k,r,"noob", "header")["card"]
            print(f"{headerid}")
            requests.post(f"https://localhost:443/game/{gameid}/cards/playing/header/{headerid}",headers=heads[k], verify=False)

        status=getStatus(gameid, heads)
        cards=status["cards"]
    
        if debug: print("----------------------- JUGAR CABECERAS -----------------------------")
        if debug: print(status["game"]["playingOrder"])
        # #################### JUGAR CARTAS DE CABECERA ###########################
        #5) jugar carta (tiene que estar en la mano del jugador, ver arriba)
        for player in status["game"]["playingOrder"]:
            utils.playCard(gameid, cards, status, heads, player, r, "noob", "header", debug=debug, stats=stats)
            
        
        status=getStatus(gameid,heads, options=["cards"])   
        cards=status["cards"]
        #--------------------------------------------------------------------------
        #----------------------------- JUGAR RESTO DE CARTAS
        #--------------------------------------------------------------------------
        if debug: print("----------------------- JUGAR CARTAS -----------------------------")
        for i in range(2):
            if debug: print(f"----------------------- TURNO {i}--------------------------------")
            status=getStatus(gameid, heads, options=["game"])   
            cards={}
            for k in heads.keys():
                result = requests.get('https://localhost:443/game/'+gameid+"/cards/player", headers=heads[k], verify=False)
                cards[k]=json.loads(result.content)[k]
            if debug: print(cards)
            if debug: print(status["game"]["playingOrder"])
            
            #Play card on turn -------------------------------------------------
            for player in status["game"]["playingOrder"]:
                utils.playCard(gameid, cards, status, heads, player, r, "noob", "postheader", debug=debug, stats=stats)
            
        if debug: print("Tiempo en acabar la ronda: ", time.process_time()-tr, "s")
    print("Tiempo en acabar la partida: ", time.process_time()-t00, "s")
    
    status=getStatus(gameid, heads, options=["score", "round", "boardmap", "game"])   
    for k in status["score"]:
        stats[k["name"]].append(k["score"])
        
#%%
#Checking NWO supremacy:
for k in status["boardmap"]["nwo"].keys():
    for j in status["boardmap"]["nwo"][k].keys():
        print(f"{j}: {status['boardmap']['nwo'][k][j]['supremacy']}")
#%%
status=getStatus(gameid, heads, options=["score", "round", "boardmap", "game"])   

scoring="Middle East"
for k in status["boardmap"]["countries"]: 
    if k["region"]==scoring:
        print(k["name"])
        print(k["influence"])
#%%
scoring="Central-North America"
for k in status["boardmap"]["countries"]: 
    if k["region"]==scoring:
        print(k["name"])
        print(k["influence"])        
#%%
status=getStatus(gameid, heads, options=["score", "round", "boardmap", "game"])   
for k in status["boardmap"]["countries"]: 
    if k["isOilProducer"]:
        print(k["name"])
        print(k["influence"])
 
#%% STATS
stats["victories"]={"EU":0, "US":0, "Russia":0, "China":0}
stats["avgVP"]={"EU":0, "US":0, "Russia":0, "China":0}
stats["sdVP"]={"EU":0, "US":0, "Russia":0, "China":0}

import numpy as np
for k in stats["victories"].keys():
    stats["sdVP"][k]=np.std(stats[k])
    stats["avgVP"][k]=np.mean(stats[k])

for i in range(len(stats["US"])):
    si={}
    for k in stats["victories"].keys():
        si[k]=stats[k][i]
    victors=[key for key, value in si.items() if value == max(si.values())]
    for v in victors:
        stats["victories"][v]+=1
#%%
import matplotlib.pyplot as plt
plt.bar(x=stats["avgVP"].keys(), height=stats["avgVP"].values() , color=["Yellow","Blue","White", "Red"], edgecolor="Grey")
plt.title("Average VPs")
#plt.xlabel("Superpower")
#%%
plt.errorbar(x=stats["avgVP"].keys(), fmt="o", y=stats["avgVP"].values(), yerr=stats["sdVP"].values())
plt.title("Average VPs ("+str(len(stats["US"]))+" games)")
