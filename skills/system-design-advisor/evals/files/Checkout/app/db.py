from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine('mysql+pymysql://checkout:secret@db/checkout')
session = Session(engine)
