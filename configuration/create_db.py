from fastapi import FastAPI
import sql_app.models as models
from sql_app.db import engine

app = FastAPI(title="Sample FastAPI Application",
              description="Sample FastAPI Application with Swagger and Sqlalchemy",
              version="1.0.0", )

models.Base.metadata.create_all(bind=engine)  # it creates the tables and the connection to the DB


def get_app():
    return app