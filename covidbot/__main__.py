import argparse
import configparser
import logging

from mysql.connector import connect, MySQLConnection

from covidbot.bot import Bot
from covidbot.covid_data import CovidData
from covidbot.file_based_subscription_manager import FileBasedSubscriptionManager
from covidbot.subscription_manager import SubscriptionManager
from covidbot.telegram_interface import TelegramInterface


def parse_config(config_file: str):
    cfg = configparser.ConfigParser()
    cfg.read(config_file)
    return cfg


def get_connection(cfg) -> MySQLConnection:
    return connect(database=cfg['DATABASE'].get('DATABASE'),
                   user=cfg['DATABASE'].get('USER'),
                   password=cfg['DATABASE'].get('PASSWORD'),
                   port=cfg['DATABASE'].get('PORT'),
                   host=cfg['DATABASE'].get('HOST', 'localhost'))


def send_correction_report(bot: TelegramInterface):
    if input("If you want to sent a correction message with the current report to all users, press Y: ") != "Y":
        exit(0)

    line = input("Message (Basic HTML allowed):\n")
    lines = []
    while True:
        if line:
            lines.append(line)
        else:
            break
        line = input()
    msg = '\n'.join(lines)

    print(f"\n\n{msg}\n\n")
    if input("Press Y to send this message: ") == "Y":
        bot.send_correction_message(msg)


# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename="bot.log")
# Also write to stderr
logging.getLogger().addHandler(logging.StreamHandler())

if __name__ == "__main__":
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--message', help='Do not start the bot but send a message to all users',
                        action='store_true')
    parser.add_argument('--migrate',
                        help='Do not start the bot but migrate users from file-based manager to database',
                        action='store_true')
    args = parser.parse_args()
    config = parse_config("config.ini")
    api_key = config['TELEGRAM'].get('API_KEY')

    with get_connection(config) as conn:
        data = CovidData(conn)
        user_manager = SubscriptionManager(conn)
        telegram_bot = TelegramInterface(Bot(data, user_manager), api_key=api_key)

        if args is None:
            telegram_bot.run()
        elif args.message:
            send_correction_report(telegram_bot)
        elif args.migrate:
            file_manager = FileBasedSubscriptionManager("user.json")
            user_manager.migrate_from(file_manager)
        else:
            telegram_bot.run()
