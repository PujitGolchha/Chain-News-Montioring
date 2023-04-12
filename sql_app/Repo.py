from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, cast, Float, desc, text
from sqlalchemy.sql import and_, except_, or_
from urllib.parse import urlparse
from datetime import datetime
from . import models, schemas

"""
    Table "Relevant Article"
"""


class RelevantArticleRepo:

    async def create(db: Session, relevantArticle: schemas.RelevantArticleBase):
        db_item = models.RelevantArticle(id=relevantArticle.id,
                                         ts=relevantArticle.ts,
                                         source=relevantArticle.source,
                                         title=relevantArticle.title,
                                         content=relevantArticle.content,
                                         RSS=relevantArticle.RSS,
                                         label=relevantArticle.label)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def fetch_by_id(db: Session, _id):
        return db.query(models.RelevantArticle).filter(models.RelevantArticle.id == _id).first()

    def fetch_source(db: Session, _source):
        return db.query(models.RelevantArticle).filter(models.RelevantArticle.RSS.like("%{source}%".format(source=_source))).all()

    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.RelevantArticle).offset(skip).limit(limit).all()

    def count_source(db: Session):
        return db.query(models.RelevantArticle.source, func.count(models.RelevantArticle.id).label("Count")).group_by(
            models.RelevantArticle.source).all()

    def daily_feed_metrics(db: Session):
        qry = db.query(
            models.RelevantArticle.RSS, func.sum(models.RelevantArticle.label).label("Count_1"),
            (func.count(models.RelevantArticle.label) - func.sum(models.RelevantArticle.label)).label("Count_0"),
            (func.sum(models.RelevantArticle.label) / func.count(models.RelevantArticle.label)).label("Avg_Daily_Hit_Rate")
        ).group_by(models.RelevantArticle.RSS, models.RelevantArticle.ts).all()

        return qry

    def source_exist(db: Session, source):
        query = db.query(
            models.RelevantArticle.RSS).filter(models.RelevantArticle.RSS == source).group_by(models.RelevantArticle.RSS).first()
        if query is None:
            return False
        else:
            return True


    def fetch_feed_metrics(db: Session, source):
        query = db.query(
            models.RelevantArticle.RSS, func.sum(models.RelevantArticle.label).label("Total_1"),
            (func.count(models.RelevantArticle.label) - func.sum(models.RelevantArticle.label)).label("Total_0"),
            (func.sum(models.RelevantArticle.label) / func.count(models.RelevantArticle.label)).label("Avg_Hit_Rate")
        ).filter(models.RelevantArticle.RSS == source).group_by(models.RelevantArticle.RSS).first()
        return query
    

    def all_feed_metrics(db: Session, hitRateThreshold, total):
        query = db.query(
            models.RelevantArticle.RSS, func.sum(models.RelevantArticle.label).label("Total_1"),
            (func.count(models.RelevantArticle.label) - func.sum(models.RelevantArticle.label)).label("Total_0"),
            (func.sum(models.RelevantArticle.label)*100 / func.count(models.RelevantArticle.label)).label("Avg_Hit_Rate"),
            (func.max(models.RelevantArticle.ts)).label("Last_Updated"))\
            .filter(or_(models.RelevantArticle.RSS.like("%http%"),models.RelevantArticle.RSS.like("%https%")))\
            .group_by(models.RelevantArticle.RSS).order_by(desc('Avg_Hit_Rate'))\
            .having(and_((func.count(models.RelevantArticle.label) > total),text(f"Avg_Hit_Rate > {hitRateThreshold}".format(hitRateThreshold)))).all()
        return query
    
    def timeFilter_feed_metrics(db: Session, start, end, hitRateThreshold, total):
        date1=datetime.strptime(start,"%Y-%m-%d").timestamp()*1000
        date2=datetime.strptime(end,"%Y-%m-%d").timestamp()*1000                                                

        # Sources which are present specified period but not the before that
        newSourcesInTimePeriod = db.query((models.RelevantArticle.RSS).label('new_sources')).\
            filter(and_(models.RelevantArticle.ts>=date1,models.RelevantArticle.ts<date2)).distinct(models.RelevantArticle.RSS)\
                .except_(db.query(models.RelevantArticle.RSS).filter(models.RelevantArticle.ts<date1).distinct(models.RelevantArticle.RSS)).all()
        
        newSourcesInTimePeriod = [item['new_sources'] for item in newSourcesInTimePeriod]

        # Feed Metrics of new sources till today
        query = db.query(models.RelevantArticle.RSS, func.sum(models.RelevantArticle.label).label("Total_1"),
            (func.count(models.RelevantArticle.label) - func.sum(models.RelevantArticle.label)).label("Total_0"),
            (func.sum(models.RelevantArticle.label)*100 / func.count(models.RelevantArticle.label)).label("Avg_Hit_Rate"),
            (func.max(models.RelevantArticle.ts)).label("Last_Updated"))\
            .filter(models.RelevantArticle.RSS.in_(newSourcesInTimePeriod))\
            .filter(or_(models.RelevantArticle.RSS.like("%http%"),models.RelevantArticle.RSS.like("%https%")))\
            .group_by(models.RelevantArticle.RSS).order_by(desc('Avg_Hit_Rate'))\
            .having(and_((func.count(models.RelevantArticle.label) > total),text(f"Avg_Hit_Rate > {hitRateThreshold}".format(hitRateThreshold)))).all()
        
        
        return query
    
    def sourceMetricsDelta(db: Session, start, end, hitRateThreshold, total):
        date1=datetime.strptime(start,"%Y-%m-%d").timestamp()*1000
        date2=datetime.strptime(end,"%Y-%m-%d").timestamp()*1000

        newSourcesInTimePeriod = db.query((models.RelevantArticle.RSS).label('new_sources')).\
            filter(and_(models.RelevantArticle.ts>=date1,models.RelevantArticle.ts<date2)).distinct(models.RelevantArticle.RSS)\
                .except_(db.query(models.RelevantArticle.RSS).filter(models.RelevantArticle.ts<date1).distinct(models.RelevantArticle.RSS)).all()
        
        newSourcesInTimePeriod = [item['new_sources'] for item in newSourcesInTimePeriod]
        

        query = db.query(models.RelevantArticle.RSS, func.sum(models.RelevantArticle.label).label("Total_1"),
            (func.count(models.RelevantArticle.label) - func.sum(models.RelevantArticle.label)).label("Total_0"),
            (func.sum(models.RelevantArticle.label)*100 / func.count(models.RelevantArticle.label)).label("Avg_Hit_Rate"),
            (func.max(models.RelevantArticle.ts)).label("Last_Updated"))\
            .filter(and_(models.RelevantArticle.ts>=date1,models.RelevantArticle.ts<date2))\
            .filter(models.RelevantArticle.RSS.in_(newSourcesInTimePeriod))\
            .filter(or_(models.RelevantArticle.RSS.like("%http%"),models.RelevantArticle.RSS.like("%https%")))\
            .group_by(models.RelevantArticle.RSS).order_by(desc('Avg_Hit_Rate'))\
            .having(and_((func.count(models.RelevantArticle.label) > total),text(f"Avg_Hit_Rate > {hitRateThreshold}".format(hitRateThreshold)))).all()
    
        
        return query


    def fetch_articles_between_dates(db: Session,date1,date2):
        date1=datetime.strptime(date1,"%Y-%m-%d").timestamp()*1000
        date2=datetime.strptime(date2,"%Y-%m-%d").timestamp()*1000
        return db.query(models.RelevantArticle).filter(and_(models.RelevantArticle.ts>=date1,models.RelevantArticle.ts<date2)).all()

    async def delete(db: Session, item_id):
        db_item = db.query(models.RelevantArticle).filter_by(id=item_id).first()
        db.delete(db_item)
        db.commit()

    async def update(db: Session, item_data):
        updated_item = db.merge(item_data)
        db.commit()
        return updated_item
    
""" 
    Location Table functions
"""
class LocationsRepo:

    async def create(db: Session, location: schemas.LocationsBase):
        db_item = models.Locations(ID= location.ID, 
                                   ts=location.ts,
                                         RSS=location.RSS,
                                         Latitude=location.Latitude,
                                         Longitude=location.Longitude,
                                         Country=location.Country,
                                         State=location.State,
                                         City=location.City
                                         )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item


    def fetch_source(db: Session, _source):
        return db.query(models.Locations).filter(models.Locations.RSS.like("%{source}%".format(source=_source))).all()

    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Locations).offset(skip).limit(limit).all()


    def source_exist(db: Session, source):
        query = db.query(models.Locations.RSS).filter(models.Locations.RSS == source).group_by(models.Locations.RSS).first()
        if query is None:
            return False
        else:
            return True

    def fetch_locations_between_dates(db: Session,date1,date2):
        date1=datetime.strptime(date1,"%Y-%m-%d").timestamp()*1000
        date2=datetime.strptime(date2,"%Y-%m-%d").timestamp()*1000
        return db.query(models.Locations).filter(and_(models.Locations.ts>=date1,models.Locations.ts<date2)).all()
    
    def num_entries(db: Session):
        return db.query(func.max(models.Locations.ID).label("max")).first()

