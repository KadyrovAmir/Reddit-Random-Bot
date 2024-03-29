from peewee import *
import environ

env = environ.Env()
environ.Env.read_env()
pg_db = PostgresqlDatabase(env('DB_DATABASE'), user=env('DB_USERNAME'), password=env('DB_PASSWORD'),
                           host=env('DB_HOST'), port=5432)


class BannedSubreddits(Model):
    id = UUIDField(primary_key=True)
    subreddit = CharField(max_length=30, unique=True)
    user = IntegerField()

    class Meta:
        database = pg_db
        db_table = 'banned_subreddits'


class MemeSubreddits(Model):
    id = UUIDField(primary_key=True)
    subreddit = CharField(max_length=30, unique=True)
    user = IntegerField()

    class Meta:
        database = pg_db
        db_table = 'meme_subreddits'
        
        
class ClientInfo(Model):
    id = UUIDField(primary_key=True)
    user_id = IntegerField()
    username = CharField(max_length=30, unique=True)
    role = CharField(max_length=30, unique=True)
    
    class Meta:
        database = pg_db
        db_table = 'client_info'

if __name__ == '__main__':
    BannedSubreddits.create_table()
    MemeSubreddits.create_table()
    ClientInfo.create_table()