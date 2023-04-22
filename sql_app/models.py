from sqlalchemy import Column, Integer, String, Float
#from sqlalchemy.orm import relationship

from sql_app.db import Base

class RelevantArticle(Base):
    __tablename__ = "RelevantArticle"

    id = Column(String, primary_key=True, index=True)
    ts = Column(Float, nullable=False)
    source = Column(String, nullable=True)
    title = Column(String, nullable=True)
    content = Column(String, nullable=True)
    RSS = Column(String, nullable=True)
    label = Column(Integer, nullable=True)



    def __repr__(self):
        return 'Relevant_ArticleModel(uuid= %s, ts = %s,  source=%s)' % (self.uuid, self.ts, self.source)


class Locations(Base):
    __tablename__ = "Locations"
    ID = Column(Integer, primary_key=True)
    RssID = Column(String, nullable=True)
    ts = Column(Float, nullable=False)
    RSS = Column(String, nullable=False)
    Latitude = Column(Float, nullable=True)
    Longitude = Column(Float, nullable=True)
    Country = Column(String, nullable=True)
    State = Column(String, nullable=True)
    City = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    state_code = Column(String, nullable=True)



    def __repr__(self):
        return 'Locations(ts = %s,  source=%s)' % ( self.ts, self.source)