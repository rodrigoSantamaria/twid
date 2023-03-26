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

class BodyBoardNwoTrackSlot(BaseModel):
    veto: str
    ahead: str
    supremacy: str
    description: str
    
    
from pydantic import BaseModel, validator

from typing import Dict, List, Optional



# Models used to validate the request body

# https://fastapi.tiangolo.com/tutorial/body/

class GameGameCardsPlayingInfluenceTargets(BaseModel):

    target: Dict[str, int]

    targetExtra: Optional[Dict[str, int]]



    def validate_influence(parent, v):

        for field in v:

            if v[field] < 0 or v[field] > 5:

                raise ValueError(f"'{parent}'.'{field}' field must be >= 0 and <= 5")



    # https://github.com/pydantic/pydantic/issues/506

    @validator('target')

    def validate_target(cls, v):

        if len(v.values()) == 0:

            raise ValueError("'target' field cannot be an empty object")

        if len(v.values()) > 1:

            raise ValueError("'target' field can only be one country")

        cls.validate_influence('target', v)

        return v

 

     #NOT SURE IF NECESSARY

     # @validator('targets')

     # def validate_target(cls, v):

     #     if len(v.values()) == 0:

     #         raise ValueError("'target' field cannot be an empty object")

     #     return v



    @validator('targetExtra')

    def validate_targetExtra(cls, v):

        cls.validate_influence('targetExtra', v)

        return v



#lista de objetivos, cada unaes un diccionario clave nombre país y valor influencia

class GameGameCardsPlayingInfluence(BaseModel):

    targets: List[GameGameCardsPlayingInfluenceTargets]



    @validator('targets')

    def validate_targets(cls, v):

        if len(v) == 0:

            raise ValueError("'targets' field cannot have 0 length")

        return v



class GameGameCardsPlayingDestabilization(BaseModel):

    target: str

    add: Optional[List[Dict[str, int]]]

    remove: Optional[List[Dict[str, int]]]



class GameGameCardsPlayingText(BaseModel):

    targets: Optional[List]

    options: Optional[List]

    players: Optional[List]

    operation: Optional[str]



class GameGameCardsPlayingScore(BaseModel):

    region: str



class GameGameCardsPlayingNwo(BaseModel):

    name: str
