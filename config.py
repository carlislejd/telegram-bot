import pymongo

from os import getenv
from dotenv import load_dotenv


load_dotenv()


def messages_collection():
    client = pymongo.MongoClient(getenv('MONGO'))
    db = client.telegram
    return db.messages