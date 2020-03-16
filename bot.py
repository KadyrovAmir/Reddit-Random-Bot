import environ
import telebot
import praw
import re
import uuid
import random
from database import MemeSubreddits, BannedSubreddits, ClientInfo
from tenacity import retry

# TODO Transactions for DB and list equality
# TODO Edit DB and set the role for me
# TODO Figure out what to do with DB properties (it resets itself constantly)

# Get token from file. Not the best option to use django environ, but hey. It works though!
env = environ.Env()
environ.Env.read_env()

bot = telebot.TeleBot(env("TELEGRAM_BOT_TOKEN"))
reddit = praw.Reddit(client_id=env('REDDIT_CLIENT_ID'),
                     client_secret=env('REDDIT_CLIENT_SECRET'),
                     user_agent='Created by Mirzik')
                     
# Some kind of cache, I dunno
image_link_check = re.compile(r'^https://(i\.imgur\.com|i\.redd\.it)/.+')
reddit_gif_formats = ['.gif', 'gifv']
banned_subreddits = [banned_sub.subreddit for banned_sub in BannedSubreddits.select()]
memes_only = {client.user_id: False for client in ClientInfo.select()}
meme_subreddits = [meme_sub.subreddit for meme_sub in MemeSubreddits.select()]


def admin_only(func):
    def wrapper(message):
        current_user = ClientInfo.get(ClientInfo.user_id == message.from_user.id)
        if current_user.role == "ADMIN":
            func(message)
        else:
            bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет доступа к этой команде".format(
                             message.from_user.first_name))
    return wrapper


def reddit_random_post(message):
    while True:
        if memes_only[message.from_user.id]:
            post = reddit.subreddit(random.choice(meme_subreddits)).random()
        else:
            post = reddit.subreddit('all').random()
        if post.subreddit.over18 or post.over_18:
            continue
        if image_link_check.match(
                post.url) and 'politic' not in post.subreddit.display_name.lower() and post.subreddit.display_name not in banned_subreddits:
            reddit_post_info = {'title': post.title,
                                'url': post.url,
                                'subreddit': post.subreddit}
            return reddit_post_info


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id not in memes_only:
        memes_only[message.from_user.id] = False
        ClientInfo(id=uuid.uuid4(), user_id=message.from_user.id, username=message.from_user.username, role="USER").save(force_insert=True)
    bot.send_message(message.chat.id,
                     'Привет, {}.\nВоспользуйся командой /next, чтобы получить новый пост с Реддита!\n\nЕсли ты хочешь посмотреть только смешнявки, воспользуйся командой /funny.\n\nПо всем вопросам обращайся сюда — @kad_ami'.format(
                         message.from_user.first_name))


@bot.message_handler(commands=['echo'])
def send_test_message(message):
    bot.send_message(message.chat.id, 'Привет, {}.\nВсё в порядке, я работаю!'.format(message.from_user.first_name))


@retry
@bot.message_handler(commands=['next'])
def new_post_from_reddit(message):
    if message.from_user.id in memes_only:
        post = reddit_random_post(message)
        if post['url'][-4:] in reddit_gif_formats:
            bot.send_animation(message.chat.id,
                               post['url'],
                               caption='{} (from /r/{})'.format(post['title'], post['subreddit']))
        else:
            bot.send_photo(message.chat.id,
                           post['url'],
                           caption='{} (from /r/{})'.format(post['title'], post['subreddit']))
    else:
        bot.send_message(message.chat.id,
                         'Привет, {}.\nЛогика бота немного поменялась, поэтому напиши /start!'.format(
                             message.from_user.first_name))


@bot.message_handler(commands=['funny'])
def get_only_memes(message):
    if message.from_user.id in memes_only:
        if memes_only[message.from_user.id]:
            memes_only[message.from_user.id] = False
            text_message = 'Режим "смешных картинок" деактивирован!\nТеперь ты будешь получать случайные посты со всего Реддита.'
        else:
            memes_only[message.from_user.id] = True
            text_message = 'Режим "смешных картинок" активирован!\nТеперь ты будешь получать только посты со смешнявками.'
        bot.send_message(message.chat.id, text_message)


@bot.message_handler(commands=['add_memes'])
def add_meme_to_list(message):
    if message.from_user.id == 501248642:
        if message.reply_to_message:
            try:
                meme_subreddit = message.reply_to_message.caption.split('/r/')[1][:-1]
                if meme_subreddit not in meme_subreddits:
                    meme_subreddits.append(meme_subreddit)
                    MemeSubreddits(id=uuid.uuid4(), subreddit=meme_subreddit, user=message.from_user.id).save(force_insert=True)
                    bot.send_message(message.chat.id, "/r/{} успешно добавлен в список!".format(meme_subreddit))
                else:
                    bot.send_message(message.chat.id, "/r/{} уже есть в списке!".format(meme_subreddit))
            except:
                bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
        else:
            bot.send_message(message.chat.id, "Отправь команду через Reply!")
    else:
        bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет права добавлять новые сабреддиты с мемами в список.".format(
                             message.from_user.first_name))


@bot.message_handler(commands=['delete_memes'])
def delete_meme_from_list(message):
    if message.from_user.id == 501248642:
        if message.reply_to_message:
            try:
                meme_subreddit = message.reply_to_message.caption.split('/r/')[1][:-1]
                if meme_subreddit in meme_subreddits:
                    meme_subreddits.remove(meme_subreddit)
                    MemeSubreddits.get(MemeSubreddits.subreddit == meme_subreddit).delete_instance()
                    bot.send_message(message.chat.id, "/r/{} успешно удалён из списка!".format(meme_subreddit))
            except:
                bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
        else:
            bot.send_message(message.chat.id, "Отправь команду через Reply!")
    else:
        bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет права удалять сабреддиты из списка с мемами.".format(
                             message.from_user.first_name))


@bot.message_handler(commands=['ban'])
def add_meme_to_list(message):
    if message.from_user.id == 501248642:
        if message.reply_to_message:
            try:
                ban_subreddit = message.reply_to_message.caption.split('/r/')[1][:-1]
                if ban_subreddit not in banned_subreddits:
                    banned_subreddits.append(ban_subreddit)
                    BannedSubreddits(id=uuid.uuid4(), subreddit=ban_subreddit, user=message.from_user.id).save(force_insert=True)
                    bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                    bot.send_message(message.chat.id, "/r/{} успешно добавлен в чёрный список!".format(ban_subreddit))
                else:
                    bot.send_message(message.chat.id, "/r/{} уже есть в чёрном списке!".format(ban_subreddit))
            except:
                bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
        else:
            bot.send_message(message.chat.id, "Отправь команду через Reply!")
    else:
        bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет права добавлять сабреддиты в чёрный список.".format(
                             message.from_user.first_name))
                             
                             
@bot.message_handler(commands=['bot_users'])
def get_all_users_of_bot(message):
    if message.from_user.id == 501248642:
        message_text = "Список пользователей бота:\n\n" + "\n".join(["@{} (id = {})".format(client.username, client.user_id) for client in ClientInfo.select()])
        bot.send_message(message.chat.id, message_text)
    else:
        bot.send_message(message.chat.id,
                         "Прости, {}, но у тебя нет доступа к этой команде".format(
                             message.from_user.first_name))


bot.polling(none_stop=True)
