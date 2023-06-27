import sqlalchemy as db
from sqlalchemy.orm import Session, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import csv


Base = declarative_base()

class Users(Base):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    image_path = db.Column(db.String, nullable=True)

    plants = relationship("Plants", backref=backref("user"))


class Plants(Base):
    __tablename__ = "Plants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    name = db.Column(db.String, nullable=False)
    botanical_name = db.Column(db.String, nullable=True)
    image_loc = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=True)
    watering = db.Column(db.String, nullable=True)
    sun_exposure = db.Column(db.String, nullable=True)
    substrate = db.Column(db.String, nullable=True) 
    soil_ph = db.Column(db.String, nullable=True)

    pots = relationship("Pots", backref=backref("plant"))

class Pots(Base):
    __tablename__= "Pots"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    plant_id = db.Column(db.Integer, db.ForeignKey("Plants.id"))
    name = db.Column(db.String, nullable=True)
    plant_name = db.Column(db.String, nullable=True)
    plant_image = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=True)
    light_intensity = db.Column(db.String, nullable=True)
    soil_moisture = db.Column(db.String, nullable=True)
    soil_moisture_range = db.Column(db.String, nullable=True)
    watering = db.Column(db.String, nullable=True)
    soil_ph = db.Column(db.String, nullable=True)

    readings = relationship("SensorReadings", backref=backref("pot"))

    
class SensorReadings(Base):
    __tablename__ = "SensorReadings"
    id = db.Column(db.Integer, primary_key=True)
    pot_id = db.Column(db.Integer, db.ForeignKey("Pots.id"))
    datetime = db.Column(db.DateTime, nullable=True)
    watering_timestamp = db.Column(db.DateTime, nullable=True)
    temperature_celsius = db.Column(db.Float, nullable=True)
    light_intensity_lux = db.Column(db.Float, nullable=True)
    soil_moisture = db.Column(db.Float, nullable=True)
    soil_ph = db.Column(db.Float, nullable=True)


db_engine = db.create_engine("sqlite:///pyflora.db")
Base.metadata.create_all(bind=db_engine)

if __name__ == "__main__":


    with Session(bind=db_engine) as session:

        user = Users(username="m", password="m", first_name="Mabel", last_name="Mora", image_path=f'./mabel_mora.jpg')
        session.add(user)

        
        with open('plants_pyflora.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                plants = Plants(user_id=row['User_ID'], name=row['Plant_name'], botanical_name=row['Plant_botanical_name'], image_loc=row['Plant_image_loc'], 
                                location=row['Plant_location'], watering=row['Watering'], sun_exposure=row['Sun_exposure'], substrate=row['Substrate'],
                                soil_ph=row['Soil_pH'])
                session.add(plants)

        session.commit()
        
