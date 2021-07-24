import os
import random
import re

import praw
import requests

from database import ClientInfo, session, BannedSubreddit, MemeSubreddit
from enums import FileContentType

IMAGE_MAX_SIZE = 5242880
GIF_MAX_SIZE = 20971520

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="RANDOM_REDDIT_BOT"
)
image_link_check = re.compile(r'^https://(i\.imgur\.com|i\.redd\.it)/.+')


def get_current_user(user_id: int) -> ClientInfo:
    return session.query(ClientInfo).filter(ClientInfo.user_id == user_id).one_or_none()


def get_reddit_random_post(user_id):
    user = session.query(ClientInfo).filter(ClientInfo.user_id == user_id).one()
    banned_subreddits = session.query(BannedSubreddit.subreddit).all()
    meme_subreddits = None

    if user.is_meme_only:
        meme_subreddits = session.query(MemeSubreddit.subreddit).filter(MemeSubreddit.user == user_id)

    while True:
        if user.is_meme_only:
            post = random.choice([submission for submission in reddit.subreddit(random.choice(meme_subreddits)).hot(limit=20)])
        else:
            post = reddit.subreddit("all").random()

        if post.subreddit.over18 or post.over_18 or not (
                image_link_check.match(post.url)
                and "politic" not in post.subreddit.display_name.lower()
                and post.subreddit.display_name not in banned_subreddits
        ):
            continue

        response = requests.get(post.url)
        size = response.headers.get("content-length")
        if size:
            size = int(size)
        else:
            continue
        content_type = response.headers.get("content-type").split("/")[-1]
        data = {
            "title": post.title,
            "url": post.url,
            "subreddit": post.subreddit
        }

        if content_type in ("jpeg", "png"):
            if size > IMAGE_MAX_SIZE:
                continue
            data["type"] = FileContentType.IMAGE
        elif content_type == "gif":
            if size > GIF_MAX_SIZE:
                continue
            data["type"] = FileContentType.GIF
        else:
            continue

        return data
