#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 11:43:25 2023

@author: rodri
"""
import random
modifiers={}
def roll(d=6):
    random.randint(1,6)
  
def modify(order, value):
    if not order in mods.keys():
        mods[order]=value
    else:
        mods[order]+=value

def getCountry(self, name):
    countriesAll = self.board_map_get()['countries']
    country = [eachCountry for eachCountry in countries if eachCountry['name'] == name]
    if len(country) < 1: return False
    else: return country[0]

    
    