from pydantic import BaseModel
from typing import Dict, List, Optional

# Models used to validate the request body
# https://fastapi.tiangolo.com/tutorial/body/
class BodyBoardScorePlayer(BaseModel):
    score: int

class BoardMapRegion(BaseModel):
    country: str

# https://stackoverflow.com/questions/68650162/fastapi-receive-list-of-objects-in-body-request
# https://stackoverflow.com/questions/60844846/read-a-body-json-list-with-fastapi
# https://stackoverflow.com/questions/58068001/python-pydantic-using-a-list-with-json-objects
class BodyBoardMapRegion(BaseModel):
    __root__: List[BoardMapRegion]

class BoardMapRegionCountryInfluence(BaseModel):
    influence: int
    extra: Dict[str, Optional[int]]
    #extra: Dict[str, int]
    #extra: Dict[str, int]

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


class BodyBoardNwoTrackSlot(BaseModel):
    veto: str
    ahead: str
    supremacy: str
    description: str