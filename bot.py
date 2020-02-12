import environ
import telebot
import praw
import re

# Get token from file. Not the best option to use django environ, but hey. It works though!
env = environ.Env()
environ.Env.read_env()

bot = telebot.TeleBot(env("TELEGRAM_BOT_TOKEN"))
reddit = praw.Reddit(client_id=env('REDDIT_CLIENT_ID'),
                     client_secret=env('REDDIT_CLIENT_SECRET'),
                     user_agent='my user agent')
image_link_check = re.compile(r'^https://(i\.imgur\.com|i\.redd\.it)/.+')

def reddit_random_post():
    has_image = False
    while not has_image:
        post = reddit.subreddit('all').random()
        if post.over_18:
            continue
        if image_link_check.match(post.url):
            image_url = post.url
            has_image = True
    reddit_post_info = {'title': post.title,
                        'url': image_url,
                        'subreddit': post.subreddit}
    return reddit_post_info


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, {}. Можем начинать!'.format(message.from_user.first_name))


@bot.message_handler(commands=['next'])
def start_message(message):
    post = reddit_random_post()
    bot.send_photo(message.chat.id, post['url'], '{} (from /r/{})'.format(post['title'], post['subreddit']))


bot.polling()
