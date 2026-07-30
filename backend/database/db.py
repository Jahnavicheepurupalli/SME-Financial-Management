import json
import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from backend.config import Config

# DB Paths
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sme_financials.db")
SQLITE_DATABASE_URI = f"sqlite:///{SQLITE_DB_PATH}"
MYSQL_DATABASE_URI = f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}"

engine = None
SessionLocal = None
is_sqlite = False

# Try connecting to MySQL
try:
    print(f"Attempting to verify/create MySQL database '{Config.MYSQL_DB}' at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}...")
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        connect_timeout=3
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
    conn.commit()
    cursor.close()
    conn.close()
    
    print("MySQL connection successful. Initializing MySQL engine...")
    engine = create_engine(MYSQL_DATABASE_URI, pool_recycle=3600, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"MySQL connection failed: {e}. Falling back to local SQLite database at {SQLITE_DB_PATH}")
    engine = create_engine(SQLITE_DATABASE_URI, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    is_sqlite = True

Base = declarative_base()

# MongoDB setup with fallback
class MockMongoCollection:
    def __init__(self, db_path, collection_name):
        self.db_path = db_path
        self.collection_name = collection_name
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({}, f)

    def _read_data(self):
        self._ensure_file()
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_data(self, data):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def insert_one(self, document):
        data = self._read_data()
        if self.collection_name not in data:
            data[self.collection_name] = []
        
        # If document doesn't have _id, generate it
        if '_id' not in document:
            from uuid import uuid4
            document['_id'] = str(uuid4())
            
        data[self.collection_name].append(document)
        self._write_data(data)
        return type('InsertOneResult', (object,), {'inserted_id': document['_id']})()

    def find_one(self, query):
        data = self._read_data()
        collection = data.get(self.collection_name, [])
        for item in collection:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                return item
        return None

    def find(self, query=None):
        data = self._read_data()
        collection = data.get(self.collection_name, [])
        if not query:
            return collection
        
        results = []
        for item in collection:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                results.append(item)
        return results

    def replace_one(self, filter_query, replacement, upsert=False):
        data = self._read_data()
        if self.collection_name not in data:
            data[self.collection_name] = []
        collection = data.get(self.collection_name, [])
        found_idx = -1
        for idx, item in enumerate(collection):
            match = True
            for k, v in filter_query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                found_idx = idx
                break
                
        if found_idx != -1:
            if '_id' not in replacement and '_id' in collection[found_idx]:
                replacement['_id'] = collection[found_idx]['_id']
            collection[found_idx] = replacement
        elif upsert:
            if '_id' not in replacement:
                from uuid import uuid4
                replacement['_id'] = str(uuid4())
            collection.append(replacement)
            
        data[self.collection_name] = collection
        self._write_data(data)
        return type('ReplaceResult', (object,), {'matched_count': 1 if found_idx != -1 else 0, 'modified_count': 1 if found_idx != -1 else 0})()

    def delete_one(self, query):
        data = self._read_data()
        collection = data.get(self.collection_name, [])
        found_idx = -1
        for idx, item in enumerate(collection):
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                found_idx = idx
                break
        if found_idx != -1:
            collection.pop(found_idx)
        data[self.collection_name] = collection
        self._write_data(data)
        return type('DeleteResult', (object,), {'deleted_count': 1 if found_idx != -1 else 0})()

    def delete_many(self, query):
        data = self._read_data()
        collection = data.get(self.collection_name, [])
        new_collection = []
        deleted_count = 0
        for item in collection:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                deleted_count += 1
            else:
                new_collection.append(item)
        data[self.collection_name] = new_collection
        self._write_data(data)
        return type('DeleteResult', (object,), {'deleted_count': deleted_count})()


class MockMongoDB:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def __getitem__(self, name):
        return MockMongoCollection(self.db_path, name)

import socket
from urllib.parse import urlparse

def is_mongo_port_open(uri):
    try:
        parsed = urlparse(uri)
        host = parsed.hostname or 'localhost'
        port = parsed.port or 27017
        
        # Test port connectivity with a 0.2-second timeout
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

# Try connecting to real MongoDB, fallback to mock if fails
mongo_client = None
mongo_db = None
is_mock_mongo = False

mock_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_mongodb.json")

print("Checking MongoDB service availability...")
if is_mongo_port_open(Config.MONGO_URI):
    try:
        print("MongoDB port is open. Initializing MongoClient...")
        mongo_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=1000)
        mongo_client.server_info()
        mongo_db = mongo_client["sme_financials"]
        print("Successfully connected to MongoDB.")
    except Exception as e:
        print(f"MongoDB connection failed on handshake: {e}. Falling back to file-based database.")
        mongo_db = MockMongoDB(mock_db_path)
        is_mock_mongo = True
else:
    print("MongoDB port is closed. Falling back to file-based database instantly.")
    mongo_db = MockMongoDB(mock_db_path)
    is_mock_mongo = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
