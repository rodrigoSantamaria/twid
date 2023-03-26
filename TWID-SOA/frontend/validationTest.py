#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 23:14:53 2023

@author: rodri
"""
from pydantic import BaseModel, ValidationError, validator
from typing import Dict, List, Optional


class BoardMapRegionCountryInfluence(BaseModel):
    influence: int
    #extra: Dict[str, Optional[int]]
    extra: Dict[str, int]

# https://stackoverflow.com/questions/63272595/is-it-possible-to-have-arbitrary-key-names-in-pydantic
class BodyBoardMapRegionCountry(BaseModel):
    stability: int
    isConflictive: bool
    isOilProducer: bool
    influence: Dict[str, Optional[BoardMapRegionCountryInfluence]]
    comments: Optional[str]
    region: Optional[str]
    name: Optional[str]
    adjacent: Optional[List]


try:
    print("trying")
    #country={'name': 'Nigeria', 'region': 'Africa', 'stability': 1, 'influence': {'US': {'influence': 1, 'extra': {}}}, 'isConflictive': True, 'isOilProducer': True, 'comments': '', 'adjacent': ['Sahel states', 'Ivory/Gold Coast', 'Cameroon']}
    country={'name': 'Afghanistan', 'region': 'Asia', 'stability': 2, 'influence': {'Russia': {'influence': 1, 'extra': {}}}, 'isConflictive': True, 'isOilProducer': False, 'comments': 'Possibly conflictive', 'adjacent': ['Stan States', 'Iran', 'Pakistan', 'China']}   
    cm=BodyBoardMapRegionCountry.parse_obj(country)
    BodyBoardMapRegionCountry.validate(country)
    print("tried")
except ValidationError as e:
    print(e)
    """
    2 validation errors for UserModel
    name
      must contain a space (type=value_error)
    password2
      passwords do not match (type=value_error)
    """
#%%