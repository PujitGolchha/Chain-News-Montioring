import sys
sys.path.append('/home/ayadav/ArticleAPI')
sys.path.append('/home/ayadav/ArticleAPI/automatize')
sys.path.append('/home/ayadav/ArticleAPI/configuration/')

from fastapi import FastAPI
import sql_app.models as models
from sql_app.db import engine

from typing import Union
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sql_app import schemas
from sql_app.db import get_db
from sql_app.Repo import RelevantArticleRepo, LocationsRepo
from sqlalchemy.orm import Session
import uvicorn
from typing import List, Optional
from configuration import create_db
import pickle
import requests
import datetime as datetime



app = create_db.get_app()


"""
Source Metrics Endpoints
"""

@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})


@app.post('/items', tags=["Article"])
async def post_items_to_db(list_item_request: List[schemas.RelevantArticleBase], db: Session = Depends(get_db)):
    for item in list_item_request:
        db_item = RelevantArticleRepo.fetch_by_id(db, _id=item.id)
        
        if db_item:
            # # feed_metrics = RelevantArticleRepo.daily_feed_metrics(db)
            
            source_ExistingArticle = RelevantArticleRepo.fetch_by_id(db, _id=item.id)

            if db_item.label == 0 and item.label == 1:
                await RelevantArticleRepo.delete(db, item.id)

            elif source_ExistingArticle.source != item.source:
                if RelevantArticleRepo.source_exist(db =db, source = item.source):
                    fetch_oldfeed_metrics= RelevantArticleRepo.fetch_feed_metrics(db, source_ExistingArticle.source)
                    fetch_newArticle_feed_metric = RelevantArticleRepo.fetch_feed_metrics(db, item.source)

                    if fetch_oldfeed_metrics.Avg_Hit_Rate < fetch_newArticle_feed_metric.Avg_Hit_Rate:
                        await RelevantArticleRepo.delete(db, item.id)
                
                    elif fetch_oldfeed_metrics.Total_Articles > fetch_newArticle_feed_metric.Total_Articles:
                        await RelevantArticleRepo.delete(db, item.id)
                    
                    else:
                        raise HTTPException(status_code=410, detail="Item already exists!")
            
                else:
                    await RelevantArticleRepo.delete(db, item.id)

            else:     
                raise HTTPException(status_code=410, detail="Item already exists!")
        await RelevantArticleRepo.create(db=db, relevantArticle=item)


@app.get('/items', tags=["Article"])
def get_all_items(name: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get all the Items stored in database
    """
    if name:
        items = []
        db_item = RelevantArticleRepo.fetch_by_id(db, name)
        items.append(db_item)
        return items
    else:
        print(type(RelevantArticleRepo.fetch_all(db)[0]))
        return RelevantArticleRepo.fetch_all(db)


@app.get('/source/', tags=["Article"])
def get_source_metrics(hitRateThreshold: Union[None, int] = 0, total: int = 100, \
    start: Union[None, str] = None, end: Union[None, str] = None, db: Session = Depends(get_db)):

    if start != None and end != None:
        return RelevantArticleRepo.timeFilter_feed_metrics(db, start, end, hitRateThreshold, total)
    
    elif (start == None and end != None):
        raise HTTPException(status_code=420, detail="Initialise start for Time-scale Source Metrics")

    elif (start != None and end == None):
        # today's date
        default_end = datetime.date.today().strftime("%Y-%m-%d")
        return RelevantArticleRepo.timeFilter_feed_metrics(db, start, default_end, hitRateThreshold, total)
   
    else:
        return RelevantArticleRepo.all_feed_metrics(db, hitRateThreshold, total)


@app.get('/sourceMetricDelta/', tags=["Article"])
def get_source_metrics_between_time_period(hitRateThreshold: Union[None, int] = 0, total: int = 100, \
    start: Union[None, str] = None, end: Union[None, str] = None, db: Session = Depends(get_db)):
    
    if start != None and end != None:
        return RelevantArticleRepo.sourceMetricsDelta(db, start, end, hitRateThreshold, total)
    
    elif (start == None and end != None):
        raise HTTPException(status_code=420, detail="Initialise start for Time-scale Source Metrics")

    elif (start != None and end == None):
        # today's date
        default_end = datetime.date.today().strftime("%Y-%m-%d")
        return RelevantArticleRepo.sourceMetricsDelta(db, start, default_end, hitRateThreshold, total)
   
    else:
        return RelevantArticleRepo.all_feed_metrics(db, hitRateThreshold, total)

        
@app.get('/getSource/{name}', tags=["Article"])
def get_articles_from_source(name: str, db: Session = Depends(get_db)):
    return RelevantArticleRepo.fetch_source(db, name)
    # return name


@app.get('/getArticles/from={date_start}_to={date_end}', tags=["Article"])
def get_articles_between_start_and_end_date(date_start: str ,date_end: str, db: Session = Depends(get_db)):
    return RelevantArticleRepo.fetch_articles_between_dates(db,date_start,date_end)


@app.delete('/deleteItem/', tags=["Article"])
async def delete_item_by_id(item_id: Optional[str] = None, db: Session = Depends(get_db)):
    db_item = RelevantArticleRepo.fetch_by_id(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found with the given ID")
    await RelevantArticleRepo.delete(db, item_id)
    return "Item deleted successfully!"


"""
Location Endpoint
"""

@app.post('/locations', tags=["Location"])
async def post_locations_to_db(list_item_request: List[schemas.LocationsBase], db: Session = Depends(get_db)):
    for item in list_item_request:
        await LocationsRepo.create(db=db, location=item)

@app.get('/numLocations', tags=["Location"])
def get_num_entries_in_locations(db: Session = Depends(get_db)):
    return LocationsRepo.num_entries(db)


@app.get('/locations/', tags=["Location"])
def get_all_locations(source: Optional[str] = None, limit: Optional[int] = 100, db: Session = Depends(get_db)):
    """
    Get all the Items stored in database
    """
    if source:
        items = []
        db_item = LocationsRepo.fetch_source(db,source)
        items.append(db_item)
        return items
    else:
        return LocationsRepo.fetch_all(db, limit=limit)
    
@app.get('/locations_between/', tags=["Location"])
def get_locations_between_time_period(start: Union[None, str] = None, end: Union[None, str] = None, db: Session = Depends(get_db)):
    
    if start != None and end != None:
        return LocationsRepo.fetch_locations_between_dates(db, start, end)
    
    elif (start == None and end != None):
        raise HTTPException(status_code=420, detail="Initialise start for Time-scale Location Metrics")

    elif (start != None and end == None):
        # today's date
        default_end = datetime.date.today().strftime("%Y-%m-%d")
        return LocationsRepo.fetch_locations_between_dates(db, start, default_end)
   
    else:
        raise HTTPException(status_code=420, detail="Initialise start for Time-scale Location Metrics")

@app.get('/agg_locations/', tags=['Location'])
def aggregate_sources_by_location(scale: Union[None, str]= None, db: Session = Depends(get_db)):
    if scale == 'state':
        return LocationsRepo.agg_location_count(db, scale)
    elif scale == 'country':
        return LocationsRepo.agg_location_count(db, scale)
    else:
        raise HTTPException(status_code=410, detail="Incorrect scale argument: scale == city or scale")
