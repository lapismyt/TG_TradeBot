import telebot
import yobit_api
import time
import os
import json

config = {}
state = 0

with open("config.dat") as f:
    for line in f.read().split("\n"):
        if ": " in line:
            data = line.split(": ")
            config[data[0].upper()] = data[1]

bot = telebot.TeleBot(config["BOT_TOKEN"])

api = yobit_api.PublicApi()
api.API_URL = ["https://yobit.net/api/3/{0}"]

def get_bal(w):
    data = json.load(open("data.json"))
    return data["bal"][w]

def set_bal(w, val):
    data = json.load(open("data.json"))
    data["bal"][w] = val
    json.dump(data, open("data.json", "w"))

def get_info(pair="doge_rur"):
    depth = api.get_pair_depth(pair)
    asks = depth["asks"]
    bids = depth["bids"]

    asks_total_price = 0
    asks_total_count = 0
    for ask in asks:
        asks_total_price += ask[0]
        asks_total_count += ask[1]
    asks_middle_price = asks_total_price / len(asks)
    asks_middle_count = asks_total_count / len(asks)

    bids_total_price = 0
    bids_total_count = 0
    for bid in bids:
        bids_total_price += bid[0]
        bids_total_count += bid[1]
    bids_middle_price = bids_total_price / len(bids)
    bids_middle_count = bids_total_count / len(bids)

    return {"asks": {"total_price": asks_total_price, "total_count": asks_total_count, "middle_price": asks_middle_price, "middle_count": asks_middle_count}, "bids": {"total_price": bids_total_price, "total_count": bids_total_count, "middle_price": bids_middle_price, "middle_count": bids_middle_count}}

def save_info(info, pair="doge_rur"):
    data = json.load(open("data.json"))
    data["history"][pair].append(info)
    json.dump(data, open("data.json", "w"))

def get_history(pair="doge_rur"):
    data = json.load(open("data.json"))
    return data["history"][pair]

def buy(price, pair="doge_rur"):
    wal = pair.split("_")
    wal1 = wal[0]
    wal2 = wal[1]
    bal1 = get_bal(wal1)
    bal2 = get_bal(wal2)
    trade_percent = int(config["TRADE_PERCENT"])
    amount = bal2 / 100 * trade_percent / price
    cost = amount * price
    bal2 -= cost
    bal1 += amount
    set_bal(wal1, bal1)
    set_bal(wal2, bal2)

def sell(price, pair="doge_rur"):
    wal = pair.split("_")
    wal1 = wal[0]
    wal2 = wal[1]
    bal1 = get_bal(wal1)
    bal2 = get_bal(wal2)
    trade_percent = int(config["TRADE_PERCENT"])
    amount = (bal1 / 100 * trade_percent) * (1 / price)
    cost = amount * price
    bal2 += cost
    bal1 -= amount
    set_bal(wal1, bal1)
    set_bal(wal2, bal2)

def buy_or_sell_old(history, bal1, bal2):
    info = history[-1]
    prev_info = history[-2]

    asks = info["asks"]
    bids = info["bids"]
    prev_asks = prev_info["asks"]
    prev_bids = prev_info["bids"]

    asks_total_price = asks["total_price"]
    asks_middle_price = asks["middle_price"]
    asks_total_count = asks["total_count"]

    bids_total_price = bids["total_price"]
    bids_middle_price = bids["middle_price"]
    bids_total_count = bids["total_count"]

    prev_asks_total_price = prev_asks["total_price"]
    prev_asks_middle_price = prev_asks["middle_price"]
    prev_asks_total_count = prev_asks["total_count"]

    prev_bids_total_price = prev_bids["total_price"]
    prev_bids_middle_price = prev_bids["middle_price"]
    prev_bids_total_count = prev_bids["total_count"]

    algorithm = int(config["ALGORITHM"])
    threshold = int(config["THRESHOLD"])
    if algorithm == 0:
        if (asks_total_price / 100 * (100 - threshold) > prev_asks_total_price):
            return 0
        elif (bids_total_price / 100 * (100 - threshold) > bids_total_price):
            return 1
        else:
            return 2
    elif algorithm == 1:
        if (asks_total_count / 100 * (100 - threshold) > prev_asks_total_count):
            return 0
        elif (bids_total_count / 100 * (100 - threshold) > prev_bids_total_count):
            return 1
        else:
            return 2
    elif algorithm == 2:
        pass
    else:
        print("Algorithm not selected")
        exit(1)

def buy_or_sell(h, bal, bal2):
    global state
    do = buy_or_sell_old(h, bal1, bal2)
    if do == 0 and state == 0:
        state = 1
        return 0
    if do == 1 and state == 1:
        state = 0
        return 1
    else:
        data = json.load(open("data.json"))
        del data["history"]["doge_rur"]
        json.dump(data, open("data.json", "w"))
        return 2

if __name__ == "__main__":
    for i in range(int(config["REPEAT"])):
        info = get_info()
        save_info(info)
        bal1 = get_bal("doge")
        bal2 = get_bal("rur")
        history = get_history()
        if i == 0:
            bot.send_message(config["ADMIN"], f"Бот запущен.")
        statistic = "Средняя цена:\n"
        statistic += f"Покупка: {str(info['asks']['middle_price'])};\n"
        statistic += f"Продажа: {str(info['bids']['middle_price'])}.\n\n"
        statistic += f"Общая стоимость всех офферов:\n"
        statistic += f"Покупка: {str(info['asks']['total_price'])};\n"
        statistic += f"Продажа: {str(info['bids']['total_price'])}.\n\n"
        statistic += f"Общее количество валюты всех офферов:\n"
        statistic += f"Покупка: {str(info['asks']['total_count'])};\n"
        statistic += f"Продажа: {str(info['bids']['total_count'])}."
        if len(history) >= 2:
            do = buy_or_sell(history, bal1, bal2)
            if do == 0:
                #buy(info["asks"]["middle_price"])
                bal1 = get_bal("doge")
                bal2 = get_bal("rur")
                bal_info = f"Баланс (вселенной):\nDOGE: {str(bal1)}\nRUR: {str(bal2)}"
                bot.send_message(config["ADMIN"], f"Покупай по {str(info['asks']['middle_price'])}.\n\n{statistic}")
            elif do == 1:
                #sell(info["bids"]["middle_price"])
                bal1 = get_bal("doge")
                bal2 = get_bal("rur")
                bal_info = f"DOGE: {str(bal1)}\nRUR: {str(bal2)}"
                bot.send_message(config["ADMIN"], f"Продавай по {str(info['bids']['middle_price'])}.\n\n{statistic}")
            else:
                bal_info = f"DOGE: {str(bal1)}\nRUR: {str(bal2)}"
                bot.send_message(config["ADMIN"], f"Ничего не делаем.\n\n{statistic}")
        time.sleep(int(config["COOLDOWN"]))
