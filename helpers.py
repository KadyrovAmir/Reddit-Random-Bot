import os
import random
import re

import praw

from database import ClientInfo, session, BannedSubreddit, MemeSubreddit

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

    if user.is_meme_only:
        meme_subreddits = session.query(MemeSubreddit.subreddit).filter(MemeSubreddit.user == user_id)
        post = reddit.subreddit(random.choice(meme_subreddits)).random()
    else:
        post = reddit.subreddit("all").random()

    while True:
        if post.subreddit.over18 or post.over_18:
            continue

        if (
                image_link_check.match(post.url)
                and "politic" not in post.subreddit.display_name.lower()
                and post.subreddit.display_name not in banned_subreddits
        ):
            return {
                "title": post.title,
                "url": post.url,
                "subreddit": post.subreddit
            }
