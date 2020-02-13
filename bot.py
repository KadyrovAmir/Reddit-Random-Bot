import logging
import environ
import telebot
import praw
import re
import os
from flask import Flask, request

# Get token from file. Not the best option to use django environ, but hey. It works though!
env = environ.Env()
environ.Env.read_env()

bot = telebot.TeleBot(env("TELEGRAM_BOT_TOKEN"))
reddit = praw.Reddit(client_id=env('REDDIT_CLIENT_ID'),
                     client_secret=env('REDDIT_CLIENT_SECRET'),
                     user_agent='Created by Mirzik')
image_link_check = re.compile(r'^https://(i\.imgur\.com|i\.redd\.it)/.+')
reddit_gif_formats = ['.gif', 'gifv']


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
    bot.send_message(message.chat.id, 'Привет, {}.\nВоспользуйся командой /next, чтобы получить новый пост с Реддита!'.format(message.from_user.first_name))
    

@bot.message_handler(commands=['echo'])
def send_test_message(message):
    bot.send_message(message.chat.id, 'Привет, {}.\nВсё в порядке, я работаю!'.format(message.from_user.first_name))


@bot.message_handler(commands=['next'])
def new_post_from_reddit(message):
    post = reddit_random_post()
    if post['url'][-4:] in reddit_gif_formats:
        bot.send_document(message.chat.id, post['url'], '{} (from /r/{})'.format(post['title'], post['subreddit']))
    else:
        bot.send_photo(message.chat.id, post['url'], '{} (from /r/{})'.format(post['title'], post['subreddit']))


bot.polling(none_stop=True)
