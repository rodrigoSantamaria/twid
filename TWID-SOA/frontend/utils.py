#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 20:57:15 2023

TODO: on define targets we may do a more precise UEmember selection based on 
current adhesions
TODO: some target definition conditions are not perfect
TODO: more intelligent moves


@author: rodri
"""
import validators
import requests
import json

#
def whoEdges(country):
    val=0
    ce=""
    for k in country["influence"].keys():
        if(country["influence"][k]["influence"]==val):
            ce=""
        elif(country["influence"][k]["influence"]>val):
            val=country["influence"][k]["influence"]
            ce=k
    return ce
#tal=whoEdges(countries[77])

def getCountry(countries, name):
    country = [eachCountry for eachCountry in countries if eachCountry['name'] == name]
    if len(country) < 1: return False
    else: return country[0]

def playerFaction(player):
    factions={"EU": "W", "US": "W", "Russia":"E", "China": "E"}
    return factions[player]

#Determines if a card being played is cancelled by some game effect (returns True) or not (False)
def cancelCard(gameid, card, player, token):
    import random
    
    #In play mods
    #print(f"Getting cars in play...")
    result = requests.get(f'https://localhost:443/game/{gameid}/cards/playing', headers=token, verify=False)
    inplay=json.loads(result.content)
    #print(f"Cards in play: {inplay}")
    
    #guantanamo
    if(66 in inplay and player!="US" and (card["type"]=="Personality" or ("subtype" in card.keys() and card["subtype"]=="Personality"))): 
        if(random.choice(["use", "keep"])=="use"):
            result = requests.delete(f'https://localhost:443/game/{gameid}/cards/playing/66', headers=token, verify=False)
            #print(f"{result}")
            return True

    #fsb
    if(15 in inplay and player!="Russia" and (card["type"]=="Personality" or ("subtype" in card.keys() and card["subtype"]=="Personality"))): 
        if(random.choice(["use", "keep"])=="use"):
            result = requests.delete(f'https://localhost:443/game/{gameid}/cards/playing/15', headers=token, verify=False)
            #print(f"{result}")
            return True
   
    #NWO mods
    result = requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False)
    boardmap=json.loads(result.content)
    nwo=boardmap["nwo"]
    #global positioning or fiscal paradises
    if(card["type"]=="Economy" or ("subtype" in card.keys() and card["subtype"]=="Economy")):
        if(nwo["Economy"]["Fiscal paradises"]["supremacy"]!=player and nwo["Economy"]["Fiscal paradises"]["supremacy"]!=""):
            if(random.choice(["use", "keep"])=="use"):
                return True
                #TODO remove supremacy
    if(card["type"]=="Personality" or ("subtype" in card.keys() and card["subtype"]=="Personality")):
        if(nwo["Technology"]["Global positioning"]["supremacy"]!=player and nwo["Technology"]["Global positioning"]["supremacy"]!=""):
            if(random.choice(["use", "keep"])=="use"):
                return True
                #TODO remove supremacy
                
    return False

"""
Returns a dict with countries that are valid for increasing influence from str {player}
using a card of int {points}, from the current state of dict{countries}
If any country is being influenced in this same operation, the list{avoid}(default: [])
must contain them to avoid domino influences.
The dict has country names as keys and the cost in points it would take to add
1 influence on it as values.
"""
def getAdjacentOrWithInfluence(countries, player, points, avoid=[]):
    print(f"Checking adjacent countries, to avoid; {avoid}")
    isCountryAdjacentOrWithInfluence = {}
    for country in countries:
        if player in country['influence'].keys() and country["influence"][player]["influence"]>0:
            cost=country["stability"]
            ep=whoEdges(country)
            if(ep!=player):
                cost+=1
            if points>=cost:
                isCountryAdjacentOrWithInfluence[country["name"]]=cost
                #print(f"Valid country: {country}")
        
            # Check the adjacent countries (unless domino effect - avoid)
            if(not country["name"] in avoid):
                for eachCountry in country['adjacent']:
                    if(not eachCountry in avoid):
                        adjacentCountry=getCountry(countries, eachCountry)
                        #print(f"{eachCountry}")
                        #print(f"{adjacentCountry}")
                        
                        cost=adjacentCountry["stability"]
                        #TODO: bool object is not subscriptable in some rare cases
                        ep=whoEdges(adjacentCountry)
                        if(ep!="" and ep!=player):
                            cost+=1
                        if points>=cost:
                            #print(f"\tValid adjacent country: {adjacentCountry['name']}")
                            isCountryAdjacentOrWithInfluence[eachCountry]=cost
            
    return isCountryAdjacentOrWithInfluence

def defineTargetNWO(gameid, playingPlayer):
    import random
    target=""
    result = requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False)
    nwo=json.loads(result.content)["nwo"]
    while(target==""):
        track=random.choice(list(nwo.keys()))
        tkeys=list(nwo[track].keys())
        
        #third option not available pre 9/11
        result = requests.get(f'https://localhost:443/game/{gameid}/board/round', verify=False)
        gameround=json.loads(result.content)["round"]
        if gameround<5:
            del tkeys[2]
        
        option=random.choice(list(nwo[track].keys()))
        
        selection=nwo[track][option]
        if(selection["veto"]=="" or selection["veto"]!=playingPlayer):
            if(selection["ahead"]==playingPlayer or selection["ahead"]==""):
                target=option
        #TODO: controlar el round para elegir la tercera opción de cada track
    return target
        
   
def chooseCard(gameid, cards, player, nround, level="dummy", phase="header", debug=False):
    import copy
    import random
    if debug: print(f"Choosing card among {cards}")
    cards0=copy.deepcopy(cards)
    
    if(nround<6 and 79 in cards0): #Card NWO is unplayable on turn 5
        cards0.remove(79)
        
    if(level=="dummy"):
        return {'card':cards0[0], 'playForText':True}
    if(level=="noob"):
        scores=[82,58,55,50,31,24,13]
        #8 econ crisis, depends on turn
        #16 only as header
        noway={"US":[3,9,10,16,18,19,20,21,23,25,30,33,48,49,53,66,68,73,80],
               "EU":[3,12,16,18,21,23,25,28,33,35,39,55,68],
               "Russia":[4,5,7,9,12,14,23,33,35,60,68,86], 
               "China":[7,9,12,14,35,43]} #cards you don't want to play for text with different players
        must={"US":[4,7,12,14,34,35,40,41,62,63,85],
               "EU":[7,9,22,34,40,62,63,85],
               "Russia":[3,10,18,25,34,36,40,44,69,84,85], 
               "China":[3,10,18,23,25,33,34,39,40,44,68,69,84,85]} #cards you want to play with different players
        scoresHand=(set(cards).intersection(set(scores)))
        if(len(scoresHand)==len(cards)+1):
            #last chance to choose a score card to avoid keeping it in hand
            return random.choice(scoresHand)
        
        bestChoices=[]
        for card in cards:
            if card in noway[player]:
                cards0.remove(card)
            if card in must[player]:
                bestChoices.append(card)
        if(len(bestChoices)>0):
            return {'card':random.choice(bestChoices),'playForText':True}
        else:
            if(len(cards0)>0):
                return {'card':random.choice(cards0), 'playForText':False}
            else:
                return {'card':random.choice(cards), 'playForText':False}
    #if level=="pro"
    
def getOpsModifiers(gameid, card, player, operation): 
    #TODO: this is not controlled in backend
    import random
    mods=0
    used=[]
    #NWO mods
    result = requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False)
    boardmap=json.loads(result.content)
    nwo=boardmap["nwo"]
    
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
            if(random.choice(["use", "keep"])=="use"): 
                mods+=2
                used.append("Sovereing funds")
    if(nwo["Public opinion"]["Information leaks"]["supremacy"]!=player and nwo["Public opinion"]["Information leaks"]["supremacy"]!=""):
        if(random.choice(["use", "keep"])=="use"): 
            mods-=2
            used.append("Information leaks")
    
    #In play mods
    result = requests.get(f'https://localhost:443/game/{gameid}/cards/playing', verify=False)
    inplay=json.loads(result.content)
    #print(f"Cards in play: {inplay}")
    #anti-globalization
    if(2 in inplay and (card["type"]=="Economy" or ("subtype" in card.keys() and card["subtype"]=="Economy"))):
        mods-=1
    #g20
    #if(16 in inplay and player==):
    #    mods+=1
    #print(f"Total modifiers: {mods}")
    ret={"mods":mods, "use":used}
    return ret
        
"""
Define a valid ("dummy" level) or more reasonable ("noob", "pro") country
for destabilization
"""
def defineCountryDestabilization(gameid, playingPlayer,level="dummy", restrictions=None):
    import random
    countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
    validCountries=[]
    
    #TODO: this might update
    UEmembers=['United Kingdom', 'Benelux', 'Denmark', 'Germany', 'France', 'Spain-Portugal', 'Italy', 'Greece']
    
    for country in countries:
        for k in country["influence"].keys():
            if(k!=playingPlayer and country["influence"][k]["influence"]>0):
                if country["name"] not in ["United States", "Russia", "China"]:
                    if country["name"] not in UEmembers:
                        #print(f"valid: {country['name']}")
                        if restrictions==None or (restrictions==12 and (country["isOilProducer"] or country["isConflictive"])):
                            validCountries.append(country)
                            break
    if(level=="dummy"):
         return random.choice(validCountries)["name"]   
    elif(level=="noob"):
        reasonableCountries=[]
        for country in validCountries:
            if((not playingPlayer in country["influence"] or country["influence"][playingPlayer]["influence"]==0) and country["stability"]<3):
                reasonableCountries.append(country)
        if(len(reasonableCountries)>0):
            return random.choice(reasonableCountries)["name"]
        else:
            return ""
    
def defineTargetsDestabilization(gameid, name, points, playingPlayer):
    import random
    countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
    country=getCountry(countries, name)
    #print(f"{country}")
    targets=[]
    for i in range(points): #a possible strategy, first add yourself always
        if(i==0):
            targets.append(playingPlayer)
            if not playingPlayer in country["influence"]:
                country["influence"][playingPlayer]={"influence":0,"extra":{}}
            country["influence"][playingPlayer]["influence"]+=1
        else:
            added=False
            while(not added):
                k=random.choice(list(country["influence"].keys()))
                if(k==playingPlayer or (k!=playingPlayer and country["influence"][k]["influence"]>0)):
                    country["influence"][k]["influence"]-=1
                    targets.append(k)
                    added=True
    return targets
    
"""
Given the int{points} of an operation by str{playingPlayer}, 
for the current str{gameid} status, returns a list[str] of target countries
into which to add 1 influence. A country may be repeated several times if the
influence points are enough. 
Edge breaking is taken into account, also domino effect is avoided.
"""
#TODO: maybe some special connection of expanded UE
def defineTargetsInfluence(gameid, points, playingPlayer,level="dummy"):
        import random
        targets=[]
        countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
        avoid=[]#To avoid domino effects
        while(points>0):
            #get random country (TODO: from valid ones: adjacent, etc)
            
            validCountries=getAdjacentOrWithInfluence(countries,playingPlayer,points, avoid)
            if(len(validCountries)==0):
                print("No more valid countries to influence, missed points: ",points)
                break
            if(level=="dummy"): #total random
                country=random.choice(list(validCountries.keys()))
            elif(level=="noob"): #invest only where we are not edging
                reasonableCountries=[]
                #print(len(validCountries)," valid Countries")
                for vc in validCountries.keys():
                    if whoEdges(getCountry(countries,vc))!=playingPlayer:
                        reasonableCountries.append(vc)
                #print(len(reasonableCountries), " reasonable countries")
                if(len(reasonableCountries)==0):
                    return targets
                country=random.choice(reasonableCountries)
                
            #We add the influence internally for further influences (it can redefine edges)
            cc=getCountry(countries, country)
            print(cc)
            if(not playingPlayer in cc["influence"].keys() or cc["influence"][playingPlayer]==0):
                cc["influence"][playingPlayer]={}
                cc["influence"][playingPlayer]["influence"]=1
                print(f"Country to avoid: {country}")
                avoid.append(country)  #its adjacent countries are not available to choose
            else:
                cc["influence"][playingPlayer]["influence"]+=1
            
            points-=validCountries[country]
            targets.append(country)
            
        return targets
        
#targets=defineTargetsInfluence("3YrWLzTk8m", 4, "EU")   
#print(targets)     
#
def defineTargetsText(gameid, card, faction, playingPlayer, playingOrder, nround, debug=False):
        import random
        players=["US","China","Russia","EU"]
        playerFaction={"US":"W","China":"E","Russia":"E","EU":"W"}
        UEmembers=[ 'United Kingdom', 'Benelux', 'Denmark', 'Germany', 'France', 'Spain-Portugal', 'Italy', 'Greece']
        east=["Russia","China"]
        west=["EU","US"]
        factions={"US": "W", "EU": "W", "Russia":"E", "China":"E"}
        ifactions={"W":["EU","US"], "E":["Russia", "China"]}
        
        
        if(debug):
            print("Checking which player resolves the card")
            print(playingPlayer)
            print(playingOrder)
        targets={"targets":[], "players":[], "operation":"", "options":[], "resolvingPlayer":""}
        if(faction=="E/W" or faction==playerFaction[playingPlayer]):
            targets["resolvingPlayer"]=playingPlayer
        else:
            for i in range(len(playingOrder)):
                p=playingOrder[i]
                if(playerFaction[p]==faction):
                    targets["resolvingPlayer"]=p
                    break
        if(debug): print("Resolving player: "+targets["resolvingPlayer"])
        
        if card == 1: #ANGOLAN CIVIL WAR
            pass
        
        elif card == 2:
            pass
            #TODO: ongoing
        
        #BLACK MONDAY (DONE)
        elif card == 3:
            pass
            
        #BORIS YELTSIN  (DONE)
        elif card == 4:
            pass            
            
        #CHECHEN WARS (DONE) 
        elif card == 5:
            pass
        
        #CONGO WARS
        elif card == 6:
            pass
        
        #DEMOCRACY IN NIGERIA (DONE)
        elif card == 7:
            pass
        
        #ECONOMIC CRISIS    
        elif card == 8:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            countriesDetail=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            #add player to remove depending on epoch
            if nround <=4:
                remBlock=east
                addBlock=west
            else:
                remBlock=west
                addBlock=east
            if(debug): print(f"Block to remove: {remBlock}")     
            #select countries with influence from E/W
            validCountries=[]
            for country in countriesDetail:
                intersection = [item for item in remBlock if item in list(country["influence"].keys())]
                if(len(intersection)>0):
                    for sel in intersection:
                        if(country["influence"][sel]["influence"]>0):
                            validCountries.append(country)
                            break
            if(debug): print(f"Number of valid countries: {len(validCountries)}")     
            validCountry=random.choice(validCountries)             
            targets["targets"].append(validCountry["name"])            
            #intersection = [item for item in remBlock if item in list(country["influence"].keys())]
            intersection = list(set(remBlock).intersection(set(validCountry["influence"].keys())))
            done=False
            if(debug): print(f"comparing {remBlock} with {validCountry['influence']}, {intersection}")
            while(done==False): 
                sel=random.choice(intersection)
                if debug: print(f"\tChoosing {sel} from {intersection}")#"{validCountry['influence'][sel]['influence']}")
                
                if(sel in validCountry["influence"].keys() and validCountry["influence"][sel]["influence"]>0):
                    targets["players"].append(sel)
                    done=True
                else:
                    intersection.remove(sel)
                    if(debug): print(f"Removing {sel} from {intersection}")
                    if(len(intersection)==0):
                        print(f"ERROR: ECONOMIC CRISIS: no {remBlock}influence in country")
                        return False
            if(debug): print("player to add")
            if(not playingPlayer in remBlock):
                targets["players"].append(playingPlayer)
            else:
                targets["players"].append(random.choice(addBlock))
        #EFTA AGREEMENT
        elif card == 9:
            pass
        
        #EL JEFE
        elif card == 10:
            pass
        
        #EMBASSY ASYLUM    
        elif card == 11:
            result = requests.get(f'https://localhost:443/game/{gameid}/deck/discarded', verify=False)
            discarded=json.loads(result.content)
            if(debug): print(f"Discarded Cards: {discarded}")
            personalities=[]
            for cardid in discarded:
                result = requests.get(f'https://localhost:443/game/{gameid}/cards/{cardid}', verify=False)
                disCard=json.loads(result.content)
                if((disCard["type"]=="Personality" or ("subtype" in disCard.keys() and disCard["subtype"]=="Personality")) and disCard["faction"]==factions[targets["resolvingPlayer"]]):
                    personalities.append(cardid)
            if(len(personalities)==0):
                print("ERROR: no playable personality in the deck")
            else:
                selection=random.choice(personalities)
                targets=defineTargetsText(gameid, selection, faction, playingPlayer, playingOrder, nround)
                targets["operation"]=selection
                
          
        #EMPIRE OF WAR
        elif card == 12:
            targets["resolvingPlayer"]="US"
            #TODO: make mandatory to be conflictive or oil producer
            name=defineCountryDestabilization(gameid, "US", "noob", restrictions=card)
            targets["targets"].append(name)
            
        #EUROPE (DONE)
        elif card == 13:
            pass
        
        #FALL OF THE BERLIN WALL 
        elif card == 14:
            targets["players"].append(targets["resolvingPlayer"])
            
        #FSB CREATION
        elif card == 15:
            pass
        
        #G20
        elif card == 16:
            print("TODO")
        
        #IMF INTERVENTION
        elif card == 17:
            print("TODO")
        
        #IMMIGRANTS
        elif card == 18:
            options=UEmembers
            for k in ["Canada", "United States"]:
                options.append(k)
            chosen=random.choice(options)
            targets["targets"].append(chosen)
            targets["operation"]=random.choice(["prevent", "leave"])
                
        #ISRAELI-PALESTINIAN WARS
        elif card == 19:
            countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            country=getCountry(countries, "Israel")
            options=[]
            if(debug): print("Israel: {country}")
            for c in country["adjacent"]:
                cc=getCountry(countries, c)
                if("US" in cc["influence"].keys() and cc["influence"]["US"]["influence"]>1):
                    options.append(c)
            if(len(options)>0):
                targets["targets"].append(random.choice(options))
                
        #KATRINA (DONE)
        elif card == 20:
            pass
        
        #KHOBAR TOWERS ATTACK
        elif card == 21:
            #TODO: Noob version
            targets["targets"].append(random.choice(["EU", "US"]))
            
        #MAASTRICH TREATY (DONE)
        elif card == 22:
            options=["Germany", "France", "Italy", "Spain-Portugal", "Benelux", "Denmark", "Greece"]
            targets["targets"].append(random.choice(options))
            options.remove(targets["targets"][0])
            targets["targets"].append(random.choice(options))
            
            
        #MADE IN CHINA (DONE)
        elif card == 23:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            targets["targets"].append(random.choice(countries))
            targets["targets"].append(random.choice(UEmembers))
            
        #MIDDLE EAST (DONE)
        elif card == 24:
            pass
        
        #MUAMMAR GADDAFI
        elif card == 25:
            pass
        
        #NEOCOLONIALISM (DONE)
        elif card == 26:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            targets["targets"].append(random.choice(countries))
            targets["players"].append("US")
            targets["targets"].append(random.choice(countries))
            targets["players"].append("EU")
            targets["options"].append(random.choice(["US","EU"])) #The third VP loss   
        
        #NEOLIBERALISM
        elif card == 27:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            targets["targets"].append(random.choice(countries))
            #TODO: per turn influence loss
            
        #NORTHERN ADHESION (DONE)
        elif card == 28:
            adhesion=["Austria", "Finland", "Sweden"]
            targets["targets"].append(random.choice(adhesion))
                
            
        #OIL CRISIS    
        elif card == 29:
            print("TODO")
        
        #OIL THIRST
        elif card == 30:
            print("TODO")
        
        #OPEC (DONE)
        elif card == 31:
            pass
            
        #OSAMA BIN LADEN            
        elif card == 32:
            targets["resolvingPlayer"]="US"
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            countriesDetail=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            while(len(targets["targets"])<1):
                country=random.choice(countriesDetail)
                if country["region"]=="Middle East" or country["name"]=="Afghanistan":
                    #TODO: total dummy - do noob version (check if there's influence)
                    targets["targets"].append(country["name"])
                    targets["players"].append(random.choice(["EU","Russia","China"]))
            if(nround>=5):
                while(len(targets["targets"])<2):
                    country=random.choice(countriesDetail)
                    if country["region"]=="Middle East" or country["name"]=="Afghanistan":
                        #TODO: total dummy - do noob version
                        targets["targets"].append(country["name"])
                        targets["players"].append("US")
                
        #PARTY CONGRESS (DONE - targets)
        elif card == 33:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            countriesDetail=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            
            choices=[]
            regions=[]
            while(len(choices)<3):
                nc=random.choice(countries)
                country=getCountry(countriesDetail, nc)
                if not country["region"] in regions:
                    choices.append(nc)  
                    regions.append(country["region"])
                
            for choice in choices:
                targets["targets"].append(choice)
             
        #PETRODOLLARS (DONE)    
        elif card == 34:
            pass
        
        #RUPERT MURDOCH        
        elif card == 35:
            options=["Mass media", "Information leaks", "State propaganda"]
            targets["targets"].append(random.choice(options))
            targets["targets"].append(random.choice(options))
            
        #RUSSIAN OLIGARCHS
        elif card == 36:
            options=["Financial markets", "Fiscal paradises", "Sovereign funds"]
            targets["targets"].append(random.choice(options))
            
            
        #RWANDAN GENOCIDE    
        elif card == 37:
            for i in ["EU", "US"]:
                if(random.choice(["yes","no"])=="yes"):
                    targets["players"].append(i)
        
        #SHOCK DOCTRINE
        elif card == 38:
            options=["add", "remove"]
            targets["operation"]=random.choice(options)
            options=["Financial markets", "Fiscal paradises", "Sovereign funds"]
            targets["targets"].append(random.choice(options))
            
            if(targets["operation"]=="remove"):
                options.remove(targets["targets"][0])
                targets["targets"].append(random.choice(options))
            
        #SLOBODAN MILOSEVIC
        elif card == 39:
            pass
        
        #SOMALI CIVIL WAR
        elif card == 40:
            pass
        
        #SOUTH LEBANON CONFLICT
        elif card == 41:
            pass
        
        #SUDAN CIVIL WARS
        elif card == 42:
            while(len(targets["players"])<2):
                choice=random.choice(["EU","US","Russia","China"])
                if(choice!=targets["resolvingPlayer"]):
                    targets["players"].append(choice)
        
        #TIANANMEN PROTESTS (DONE)
        elif card == 43:
            pass
        
        #UNCOMFORTABLE DEMOCRACIES
        elif card == 44:
            options=["Venezuela", "Ecuador", "Bolivia", "Brazil", "Argentina"]
            options2=["Israel", "Ukraine"]
            operation=["add","remove"]
            
            targets["operation"]=random.choice(operation)
            if(targets["operation"]=="add"):
                targets["targets"].append(random.choice(options))
            else:
                targets["targets"].append(random.choice(options2))
                players.remove(playingPlayer)
                targets["players"].append(random.choice(players))
            
        #WOLFWOVITZ DOCTRINE
        elif card == 45:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            targets["targets"].append(random.choice(countries))
            targets["targets"].append(random.choice(countries))
            players.remove(playingPlayer)
            
            targets["players"].append(random.choice(players))
            targets["players"].append(random.choice(players))
            #TODO: check they are conflictive/oilprod
            
            
       #YUGOSLAV WARS (DONE)
        elif card == 46:
            pass
        
        #9/11 ATTACKS (DONE)
        elif card == 47:
            targets["targets"].append(random.choice(UEmembers))
            newChoice=random.choice(UEmembers)
            while(newChoice==targets["targets"][0]): #choose another
                newChoice=random.choice(UEmembers)
            targets["targets"].append(newChoice)
                
            
        #ABM TREATY WITHDRAWAL
        elif card == 48:
            pass
        
        #ABU GRAHIB (DONE)
        elif card == 49:
            pass
        
        #AFRICA
        elif card == 50:
            pass
        
        #AFRICAN UNION
        elif card == 51:
            countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            option=""
            while(option==""):
                c=random.choice(countries)
                if(c["region"]=="Africa" and c["name"]!="Morocco"):
                    option=c["name"]
                    targets["targets"].append(option)
        #AL QAEDA
        elif card == 52:
            print("TODO")
        
        #ALBA (DONE)
        elif card == 53:
            options=['Venezuela', 'Ecuador', 'Bolivia', 'Cuba', 'Honduras']
            targets["targets"].append(random.choice(options))
            options.remove(targets["targets"][0])
            targets["targets"].append(random.choice(options))
            
        
        #ARAB SPRING(DONE)
        elif card == 54:
            options=['Egypt', 'Tunisia']
            options2=['Morocco', 'Saudi Arabia', 'Gulf States']
            choice=[1,2]
            operation=random.choice(choice)
            if(choice==1):
                targets["targets"].append(random.choice(options))
            else:
                targets["targets"].append(random.choice(options2))
                targets["players"].append(random.choice(["EU","US"]))
            
        #ASIA (DONE)
        elif card == 55:
            pass
        
        #AUSTERITY PLANS (DONE)
        elif card == 56:
            targets["targets"].append(random.choice(UEmembers))
            targets["players"].append("US")
            targets["targets"].append(random.choice(UEmembers))
            targets["players"].append("EU")
            
            newChoice=random.choice(UEmembers)
            while(newChoice==targets["targets"][1]): #choose another
                newChoice=random.choice(UEmembers)
            targets["targets"].append(newChoice)
            targets["players"].append("EU")
            
        #BRICS (DONE)
        elif card == 57:
            pass
        
        #CENTRAL/NORTH AMERICA (DONE)
        elif card == 58:
            pass
        
        #CLIMATE CHANGE (DONE)
        elif card == 59:
            pass
        
        #COLOR REVOLUTION (DONE)         
        elif card == 60:
            options=['Caucasus States', 'Ukraine', 'Balkan States', 'Stan States']
            targets["targets"].append(random.choice(options))
            
        #EASTERN ADHESION (DONE)
        elif card == 61:
            adhesion=["Hungary", "Poland"]
            targets["targets"].append(random.choice(adhesion))
            targets["players"].append(random.choice(["EU","US"]))
            
        #ECONOMIC RESCUE (DONE)
        elif card == 62:
            options=['South Korea', 'Indonesia', 'Thailand', 'Philippines', 'Greece', 'Italy', 'Spain-Portugal']
            #TODO: no south america
            targets["targets"].append(random.choice(options))
            
        #FOIA
        elif card == 63:
            pass
        
        #FUCK THE EU (DONE)
        elif card == 64:
            options=['Benelux', 'France', 'Germany', 'Italy']
            targets["targets"].append(random.choice(options))
            
        #GLOBALIZATION    
        elif card == 65:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            for sp in players:
                targets["targets"].append(random.choice(countries))
                targets["players"].append(sp)
            targets["targets"].append(random.choice(countries))
            targets["players"].append(targets["resolvingPlayer"])
        
        #GUANTANAMO
        elif card == 66:
            pass
        
        #HEZBOLLAH
        elif card == 67:
            print("TODO")
        
        #HU JINTAO
        elif card == 68:
            countries=requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False).json()["countries"]
            remCountries=[]
            addCountries=[]
            for country in countries:
                if(country["region"] in ["Asia", "Africa", "South Ameria", "North-Central America"] and not country["name"] in ["US", "Russia"]):
                    addCountries.append(country["name"])
                if(whoEdges(country)=="China"):
                    remCountries.append(country["name"])
            if(debug): print(f"Countries to remove: {remCountries}")
            if(len(remCountries)>=2):
                points=1
                for i in range(2):
                    targets["targets"].append(random.choice(remCountries))
                    remCountries.remove(targets["targets"][i])
                    country=getCountry(countries, targets["targets"][i])
                    points+=country["influence"]["China"]["influence"]
                for i in range(points):
                    targets["targets"].append(random.choice(addCountries))
                    addCountries.remove(targets["targets"][2+i])
            else:
                 print("ERROR: HU JINTAO: there are no 2 countries edged by China")
        #HUGO CHAVEZ
        elif card == 69:
            targets["players"].append(random.choice(ifactions["W"]))
            
        #INVASION OF AFGHANISTAN
        elif card == 70:
            pass
        
        #INVASION OF CRIMEA (DONE)
        elif card == 71:
            pass
        
        #IRAQ WAR (DONE)
        elif card == 72:
            pass
        
        #JULIAN ASSANGE (DONE)    
        elif card == 73:
            pass
        
        #KIM JONG IL
        elif card == 74:
            pass
        
        #KYOTO PROTOCOL (DONE)
        elif card == 75:
            options=["Financial markets", "Fiscal paradises", "Sovereign funds", "Communications", "Global positioning", "Drones"]
            result = requests.get(f'https://localhost:443/game/{gameid}/board/map', verify=False)
            boardmap=json.loads(result.content)
            nwo=boardmap["nwo"]
            
            for k in ["EU","US","China","Russia"]:
                options=[]
                for track in ["Economy","Technology"]:
                    for i in nwo[track].keys():
                        if(nwo[track][i]["supremacy"]==k):
                            options.append(i)
                            
                targets["players"].append(k)
                if(len(options)>0):
                    targets["options"].append("yes")
                    targets["targets"].append(random.choice(options))
                else:
                    targets["options"].append("no")
                    targets["targets"].append("")
                    
        #LYBIAN CIVIL WAR
        elif card == 76:
            pass
        
        #NEW START (DONE)
        elif card == 77:
            options=["Financial markets", "Fiscal paradises", "Sovereign funds", "Communications", "Global positioning", "Drones"]
            for k in ["US","Russia"]:
                targets["options"].append(random.choice(["remove","no remove"]))
                targets["targets"].append(random.choice(options))
            #TODO: check supremacy
            
        #NORD STREAM 1
        elif card == 78:
            ##del UEmembers[0]
            ue=random.choice(UEmembers)
            while(ue=="United Kingdom"): #choose another
                ue=random.choice(UEmembers)
            targets["targets"].append(ue)
       
        #NWO
        elif card == 79:
            if(nround>=6):
                pass
            else:
                print("ERROR: can only be selected by text on turns 6-8")
                return False
        
        #PRISM (DONE)
        elif card == 80:
            f=open("countries.txt")
            countries=[x.replace("\n","") for x in f.readlines()]
            targets["targets"].append(random.choice(countries))
            #TODO: check UE has influence
            
        #SECOND EASTERN ADHESION (DONE)
        elif card == 81:
            adhesion=["Romania", "Bulgaria"]
            targets["targets"].append(random.choice(adhesion))
            
        #SOUTH AMERICA (DONE)
        elif card == 82:
            pass
        
        #SYRIAN CIVIL WAR (DONE)
        elif card == 83:
            pass
        
        #THE KIRCHNERS
        elif card == 84:
            options=["Argentina", "Chile", "Uruguay", "Paraguay"]
            targets["targets"].append(random.choice(options))
        
        #THE MOTHER OF ALL WARS
        elif card == 85:
            name=defineCountryDestabilization(gameid, playingPlayer, "noob")
            targets["targets"].append(name)
            
        #VIKTOR YUSHCHENKO (DONE)
        elif card == 86:
            pass
        
        #VLADIMIR PUTIN    
        elif card == 87:
            pass
        
        #WAR ON TERROR
        elif card == 88:
            pass
        
        else:
            return False #card id not found
        
        return targets
"""
Plays a card for {player} in game {gameid}.
gameid - id of the game which is being played
cards - dictionary with cards as returned by test.getStatus ("cards")
status - dictionary with game status as returned by test.getStatus ("game")
TODO: the above may be refactored better
heads - dictionary with access tokens for each player (TODO: refactor)
player - string with the name of the player (either US, EU, Russia or China)
r - round from 1 to 8
level - string with "dummy" "noob" or "expert" (TODO: implement expert)
phase - either "header" or "postheader" (default)
""" 
def playCard(gameid, cards, status, heads, player, r, level="noob", phase="postheader", debug=False, stats=None):
     import random
     
     if phase=="header":
         if debug: print(status["headerCards"][player])
         cardid=status["headerCards"][player]
         head=heads[player]
         result = requests.get(f'https://localhost:443/game/{gameid}/cards/{cardid}', verify=False)
         card=json.loads(result.content)
         if debug: print(f"{player} plays {card}")
         if debug: print(player+" plays "+str(cardid)+ " - "+card["title"])
         
         if(card["points"]==0): #PLAY FOR SCORE ###################################
             if debug: print("\tSCORING CARD")
             if stats!=None: stats["scores"][card["title"]][len(stats["scores"][card["title"]])-1]+=1
             result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/score/"+str(cardid), json={"region":card["title"]}, headers=head, verify=False)
         else:
             #PLAY FOR TEXT ###################################################<<<<<<<<<<<<<<<
             targets=defineTargetsText(gameid, cardid, card["faction"], player,status["game"]["playingOrder"],r)
             if debug: print("\t for Text:", card["title"])
             if debug: print("\t on", targets)
             
             result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/text/"+str(cardid), json=targets, headers=head, verify=False)
             if(cardid in [12,85]): #add then empire of war
                 if(debug): print("MOTHER OF ALL WARS")
                 if(result.status_code!=200):
                     print("ERROR in 1st destabilization phase") 
                     print(result)
                     print(result.content)
                     raise StopIteration()
                 if(debug): print(f'{result.content}')
                 if(eval(result.content)!=False):
                     points=int(eval(result.content))
                     if(debug): print(f"DESTABILIZATION FOR {points} points")
                     if(points>0):
                         country=targets["targets"][0]
                         if(debug): print(f"On {country}")
                         targets=defineTargetsDestabilization(gameid, country, points, player)
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/destabilization/"+str(cardid), json={"target":country, "targets":targets}, headers=head, verify=False)
                 else:
                    print("Failed destabilization (roll<=0)")
                 if(debug): print("Destabilizacion ended")
       
         if(result.status_code!=200):
             print(result)
             print(result.content)
             raise StopIteration()
         
     else:
         chosenCard=chooseCard(gameid,cards[player]["hand"],player,r,level, phase)
         cardid=chosenCard["card"]
         head=heads[player]
         result = requests.get(f'https://localhost:443/game/{gameid}/cards/{cardid}', verify=False)
         card=json.loads(result.content)
         
         if debug: print("\n"+player+" plays "+str(cardid)+": "+card["title"])
         
         if(not cancelCard(gameid, card, player, head)):
             #pbefore=[k for k in getStatus(gameid, heads, options=["score"])["score"]]
             if(card["points"]==0):
                 if debug: print("\tto score")
                 if stats!=None: stats["scores"][card["title"]][len(stats["scores"][card["title"]])-1]+=1
                 result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/score/"+str(cardid), headers=head, json={"region":card["title"]},verify=False)
             else:
                 playFor=random.choice(["influence", "destabilization"])
                 if(chosenCard["playForText"]): #PLAY FOR TEXT ###################################################
                     targets=defineTargetsText(gameid, cardid, card["faction"], player,status["game"]["playingOrder"],r)
                     if debug: print("\t for TEXT:", card["title"])
                     if debug: print("\t on", targets)
                     if(targets!=False):
                         playFor="text"
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/text/"+str(cardid), json=targets, headers=head, verify=False)
                         #minor peculiarities
                         if(debug): print(f"checking minor")
                         if(cardid in [12,85]): #add then empire of war
                             if(debug): print("MOTHER OF ALL WARS")
                             if(debug): print(f"{result.content}")
                             if(debug): print(f"{result.status_code}")
                             if(result.status_code!=200):
                                 print("ERROR in 1st destabilization phase") 
                                 print(result)
                                 print(result.content)
                                 raise StopIteration()
                             points=int(eval(result.content))
                             if(debug): print(f"DESTABILIZATION FOR {points} points")
                             if(points>0):
                                 country=targets["targets"][0]
                                 if(debug): print(f"On {country}")
                                 targets=defineTargetsDestabilization(gameid, country, points, player)
                                 result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/destabilization/"+str(cardid), json={"target":country, "targets":targets}, headers=head, verify=False)
                             if(debug): print("Destabilizaciont ended")
                             
                 elif(playFor=="influence"):#If not play it for influence or NWO
                     opmod=getOpsModifiers(gameid, card, player,"influence")
                     points=card["points"]+opmod["mods"]
                     targets=defineTargetsInfluence(gameid, points, player,level)
                     tlist=[]
                     
                     if(len(targets)==0): #PLAY FOR NWO if no country available/reasonable -------
                         target=defineTargetNWO(gameid, player)
                         if debug: print("\tfor NWO on "+target)
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/nwo/"+str(cardid), headers=head, json={"name":target},verify=False)
                     
                     else:    #PLAY FOR INFLUENCE ########################################################################
                         if debug: print("\tfor INFLUENCE with", card["points"])
                         for t in targets:
                             tlist.append({"target":{t:1}})
                         if debug: print("\t on", targets)
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/influence/"+str(cardid), json={"targets":tlist, "used":opmod["use"]}, headers=head, verify=False)
                
                 elif(playFor=="destabilization"):#Let's go for destabilization
                     country=defineCountryDestabilization(gameid, player, level)
                     if(country==""): #PLAY FOR NWO if no country available/reasonable ----------
                         target=defineTargetNWO(gameid, player)
                         if debug: print("\tfor NWO on "+target)
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/nwo/"+str(cardid), headers=head, json={"name":target},verify=False)
                     else:
                         if(debug): print(f"\tfor COUP in {country}") #PLAY FOR DESTABILIZATION ################################
                         result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/destabilization/"+str(cardid), json={"target":country}, headers=head, verify=False)
                         if(result.status_code!=200):
                             print("ERROR in 1st destabilization phase") 
                             print(result)
                             print(result.content)
                             raise StopIteration()
                         if(debug): print(f"DESTABILIZATION FOR {result.content} points")
                         points=int(eval(result.content))
                         if(points>0):
                             targets=defineTargetsDestabilization(gameid, country, points, player)
                             if(debug): print(f"\tTargets: {targets}")
                             result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/destabilization/"+str(cardid), json={"target":country, "targets":targets}, headers=head, verify=False)
                             
    
         else:        #Even if cancelled, still must be played
             if(debug): print("\tCard cancelled")
             result = requests.post('https://localhost:443/game/'+gameid+"/cards/playing/cancel/"+str(cardid), headers=head, verify=False)
         #pafter=[k for k in getStatus(gameid, heads, options=["score"])["score"]]
         #print(pafter)
         if(result.status_code!=200):
             print(result)
             print(result.content)
             raise StopIteration()
     return True