from app.db.utils import serialize_item, serialize_items
from app.db import DB
from datetime import datetime
from bson import ObjectId

# Class Collection Name
CLASS_COLLECTION = "classes"

# Class fields
TITLE = "title"
TRAINER_ID = "trainer_id"
TRAINER_NAME = "trainer_name"
START_DATE = "start_date"
END_DATE = "end_date"
CAPACITY = "capacity"
LOCATION = "location"
DESCRIPTION = "description"
CREATED_AT = "created_at"


class ClassResource:

    def __init__(self):
        self.collection = DB.get_collection(CLASS_COLLECTION)

    def create_class(self, title: str, trainer_id: str, trainer_name: str, 
                     start_date: datetime, end_date: datetime, capacity: int, 
                     location: str, description: str):
        """Create a new fitness class"""
        fitness_class = {
            TITLE: title,
            TRAINER_ID: trainer_id,
            TRAINER_NAME: trainer_name,
            START_DATE: start_date,
            END_DATE: end_date,
            CAPACITY: capacity,
            LOCATION: location,
            DESCRIPTION: description,
            CREATED_AT: datetime.now()
        }
        result = self.collection.insert_one(fitness_class)
        return result.inserted_id

    def get_upcoming_classes(self):
        """Get all upcoming classes"""
        now = datetime.now()
        classes = self.collection.find({START_DATE: {"$gte": now}}).sort(START_DATE, 1)
        return serialize_items(list(classes))

    def get_class_by_id(self, class_id: str):
        """Get class by ID"""
        try:
            fitness_class = self.collection.find_one({"_id": ObjectId(class_id)})
            return serialize_item(fitness_class)
        except:
            return None

    def get_classes_by_trainer(self, trainer_id: str):
        """Get all classes for a specific trainer"""
        classes = self.collection.find({TRAINER_ID: trainer_id})
        return serialize_items(list(classes))

    def check_trainer_overlap(self, trainer_id: str, start_date: datetime, end_date: datetime):
        """Check if trainer has overlapping classes"""
        overlapping = self.collection.find_one({
            TRAINER_ID: trainer_id,
            START_DATE: {"$lt": end_date},
            END_DATE: {"$gt": start_date}
        })
        return overlapping is not None

    def delete_all_classes(self):
        """Delete all classes (for testing)"""
        self.collection.delete_many({})
