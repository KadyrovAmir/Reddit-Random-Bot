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
                     user_agent='Created by Mirzik')
image_link_check = re.compile(r'^https://(i\.imgur\.com|i\.redd\.it)/.+')
reddit_gif_formats = ['.gif', 'gifv']
banned_subreddits = ['RoastMe']
memes_only = {}
meme_subreddits = ['youngpeopleyoutube', 'Tinder']


def reddit_random_post():
    while True:
        post = reddit.subreddit('all').random()
        if post.over_18:
            continue
        if image_link_check.match(post.url) and not 'politic' in post.subreddit.display_name.lower() and not post.subreddit.display_name in banned_subreddits:
            reddit_post_info = {'title': post.title,
                                'url': post.url,
                                'subreddit': post.subreddit}
            return reddit_post_info


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id not in memes_only:
        memes_only[message.from_user.id] = False
    bot.send_message(message.chat.id,
                     'Привет, {}.\nВоспользуйся командой /next, чтобы получить новый пост с Реддита!'.format(
                         message.from_user.first_name))


@bot.message_handler(commands=['echo'])
def send_test_message(message):
    bot.send_message(message.chat.id, 'Привет, {}.\nВсё в порядке, я работаю!'.format(message.from_user.first_name))


@bot.message_handler(commands=['next'])
def new_post_from_reddit(message):
    post = reddit_random_post()
    if post['url'][-4:] in reddit_gif_formats:
        bot.send_animation(message.chat.id,
                           post['url'],
                           caption='{} (from /r/{})'.format(post['title'], post['subreddit']))
    else:
        bot.send_photo(message.chat.id,
                       post['url'],
                       caption='{} (from /r/{})'.format(post['title'], post['subreddit']))


@bot.message_handler(commands=['enable_memes'])
def get_only_memes(message):
    print(message.from_user.id)
    if memes_only[message.from_user.id]:
        memes_only[message.from_user.id] = False
        text_message = 'Режимом мемов деактивирован!\n Теперь ты будешь получать случайные посты со всего Реддита.'
    else:
        memes_only[message.from_user.id] = True
        text_message = 'Режимом мемов активирован!\n Теперь ты будешь получать только посты с мемами.'
    bot.send_message(message.chat.id, text_message)


@bot.message_handler(commands=['enable_memes'])
def get_only_memes(message):
    if memes_only[message.from_user.id]:
        memes_only[message.from_user.id] = False
        text_message = 'Режим мемов деактивирован!\n Теперь ты будешь получать случайные посты со всего Реддита.'
    else:
        memes_only[message.from_user.id] = True
        text_message = 'Режим мемов активирован!\n Теперь ты будешь получать только посты с мемами.'
    bot.send_message(message.chat.id, text_message)


@bot.message_handler(commands=['add_memes'])
def add_meme_to_list(message):
    if message.from_user.id == 501248642:
        if message.reply_to_message:
            meme_subreddit = message.reply_to_message.caption.split('/r/')[1][:-1]
            meme_subreddits.append(meme_subreddit)
            bot.send_message(message.chat.id, "/r/{} успешно добавлен в список!".format(meme_subreddit))
        else:
            print(None)
    else:
        bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет права добавлять новые сабреддиты с мемами в список.".format(
                             message.from_user.first_name))


bot.polling(none_stop=True)
