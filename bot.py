import os
from functools import wraps
import telebot
from database import MemeSubreddit, BannedSubreddit, ClientInfo, session, Base, engine
from helpers import get_current_user, get_reddit_random_post

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))


def admin_only(func):
    @wraps(func)
    def wrapper(message):
        current_user = session.query(ClientInfo).filter(ClientInfo.user_id == message.from_user.id).one()
        if current_user.is_admin:
            func(message)
        else:
            bot.send_message(
                message.chat.id,
                f"Прости, {message.from_user.first_name}, но у тебя нет доступа к этой команде"
            )
    return wrapper


@bot.message_handler(commands=["start"])
def start_message(message):
    user = get_current_user(message.from_user.id)
    if not user:
        session.add(ClientInfo(user_id=message.from_user.id, username=message.from_user.username))
        session.commit()

    bot.send_message(
        message.chat.id,
        (
            f'Привет, {message.from_user.first_name}.\n'
            f'Воспользуйся командой /next, чтобы получить новый пост с Reddit!\n\n'
            f'Если ты хочешь посмотреть только смешнявки, воспользуйся командой /funny.\n\n'
            f'По всем вопросам обращайся сюда — @kad_ami'
        )
    )


@bot.message_handler(commands=["echo"])
def send_test_message(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}.\nВсё в порядке, я работаю!")


@bot.message_handler(commands=["next"])
def new_post_from_reddit(message):
    reddit_gif_formats = [".gif", "gifv"]
    post = get_reddit_random_post(message.from_user.id)

    if post["url"][-4:] in reddit_gif_formats:
        bot.send_animation(
            message.chat.id,
            post["url"],
            caption=f"{post['title']}\n\n(from /r/{post['subreddit']})"
        )
    else:
        bot.send_photo(
            message.chat.id,
            post["url"],
            caption="{post['title']} (from /r/{post['subreddit']})"
        )


@bot.message_handler(commands=["funny"])
def toggle_memes_only(message):
    user = get_current_user(message.from_user.id)
    if user.is_meme_only:
        user.is_meme_only = False
        text_message = 'Режим "смешных картинок" деактивирован!\nТеперь ты будешь получать случайные посты со всего Реддита.'
    else:
        user.is_meme_only = True
        text_message = 'Режим "смешных картинок" активирован!\nТеперь ты будешь получать только посты со смешнявками.'
    session.commit()
    bot.send_message(message.chat.id, text_message)


@bot.message_handler(commands=["add_memes"])
def add_meme_to_list(message):
    if message.reply_to_message:
        meme_subreddits = session.query(MemeSubreddit).filter(MemeSubreddit.user == message.from_user.id).all()
        try:
            meme_subreddit = message.reply_to_message.caption.split("/r/")[1][:-1]
            if meme_subreddit not in {subreddit.subreddit for subreddit in meme_subreddits}:
                session.add(MemeSubreddit(subreddit=meme_subreddit, user=message.from_user.id))
                session.commit()
                bot.send_message(message.chat.id, f"/r/{meme_subreddit} успешно добавлен в список!")
            else:
                bot.send_message(message.chat.id, f"/r/{meme_subreddit} уже есть в списке!")
        except:
            bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
    else:
        bot.send_message(message.chat.id, "Отправь команду через Reply!")


@bot.message_handler(commands=["delete_memes"])
def delete_meme_from_list(message):
    if message.reply_to_message:
        meme_subreddits = session.query(MemeSubreddit).filter(MemeSubreddit.user == message.from_user.id).all()
        try:
            meme_subreddit = message.reply_to_message.caption.split("/r/")[1][:-1]
            if meme_subreddit in {subreddit.subreddit for subreddit in meme_subreddits}:
                (
                    session
                    .query(MemeSubreddit)
                    .filter(MemeSubreddit.user == message.from_user.id, MemeSubreddit.subreddit == meme_subreddit)
                    .delete()
                )
                session.commit()
                bot.send_message(message.chat.id, f"/r/{meme_subreddit} успешно удалён из списка!")
            else:
                bot.send_message(message.chat.id, f"/r/{meme_subreddit} не найден в списке!")
        except:
            bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
    else:
        bot.send_message(message.chat.id, "Отправь команду через Reply!")


@bot.message_handler(commands=["ban"])
@admin_only
def ban_subreddit(message):
    if message.reply_to_message:
        banned_subreddits = session.query(BannedSubreddit).all()
        try:
            ban_subreddit = message.reply_to_message.caption.split('/r/')[1][:-1]
            if ban_subreddit not in {subreddit.subreddit for subreddit in banned_subreddits}:
                session.add(BannedSubreddit(subreddit=ban_subreddit, user=message.from_user.id))
                bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                bot.send_message(message.chat.id, f"/r/{ban_subreddit} успешно добавлен в чёрный список!")
            else:
                bot.send_message(message.chat.id, f"/r/{ban_subreddit} уже есть в чёрном списке!")
        except:
            bot.send_message(message.chat.id, "Что-то пошло не так!\nНе удалось обновить список!")
    else:
        bot.send_message(message.chat.id, "Отправь команду через Reply!")
                             
                             
@bot.message_handler(commands=["bot_users"])
@admin_only
def get_all_users_of_bot(message):
    message_text = "Список пользователей бота:\n\n" + "\n".join(
        [f"@{client.username} | (ID = {client.user_id})" for client in session.query(ClientInfo).all()]
    )
    bot.send_message(message.chat.id, message_text)


if __name__ == '__main__':
    print("Starting DB creation...")
    Base.metadata.create_all(engine)
    print("Finished DB creation...")
    print("Bot is starting...")
    bot.polling(none_stop=True)
