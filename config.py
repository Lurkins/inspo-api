import datetime

class Config(object):
    DEBUG = False
    TESTING = False

    MONGO_DBNAME = 'restdb'
    MONGO_URI = 'mongodb://localhost:27017/restdb'
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)
    

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    MONGO_DBNAME = 'restdb'
    MONGO_URI = 'mongodb://localhost:27017/restdb'

class TestingConfig(Config):
    TESTING = True

    MONGO_DBNAME = 'restdb'
    MONGO_URI = 'mongodb://localhost:27017/restdb'