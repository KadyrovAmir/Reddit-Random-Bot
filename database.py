import os

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Integer, Boolean, create_engine


engine = create_engine(
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class BannedSubreddit(Base):
    __tablename__ = "banned_subreddits"

    id = Column(Integer, primary_key=True)
    subreddit = Column(String(30), unique=True)
    user = Column(Integer, unique=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id=}, {self.subreddit=}, {self.user=})"


class MemeSubreddit(Base):
    __tablename__ = "meme_subreddits"

    id = Column(Integer, primary_key=True)
    subreddit = Column(String(30), unique=True)
    user = Column(Integer, unique=True)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id=}, {self.subreddit=}, {self.user=})"
        
        
class ClientInfo(Base):
    __tablename__ = "client_info"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String(255), unique=True)
    is_admin = Column(Boolean, default=False)
    is_meme_only = Column(Boolean, default=False)

    def __repr__(self):
        return (f"{self.__class__.__name__}({self.id=}, {self.user_id=}, "
                f"{self.username=}, {self.is_admin=}, {self.is_meme_only})")
