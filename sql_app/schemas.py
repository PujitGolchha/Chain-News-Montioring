from typing import List, Optional

from pydantic import BaseModel

"""
    Table "Relevant Article"
"""
class RelevantArticleBase(BaseModel):
    id: str
    ts: float

    source: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    RSS: Optional[str] = None
    label: Optional[int] = None

class RelevantArticleCreate(RelevantArticleBase):
    pass

class RelevantArticle(RelevantArticleBase):
    id: str

    class Config:
        orm_mode = True

"""
    Table "Location"
"""

class LocationsBase(BaseModel):
    ID: int
    ts: float
    RSS: str
    RssID: Optional[str] = None

    
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    Country: Optional[str] = None
    State: Optional[str] = None
    City: Optional[str] = None
    country_code: Optional[str] = None
    state_code: Optional[str] = None
