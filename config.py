import pymongo
from os import getenv
from dotenv import load_dotenv


load_dotenv()


def messages_collection():
    client = pymongo.MongoClient(getenv('MONGO'), ssl=True, ssl_cert_reqs='CERT_NONE')
    db = client.telegram
    return db.messages



