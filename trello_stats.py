import trello as trello_api
from win_trello import *
import os
import time
import datetime
import re
import plt_data

def smart_time(matches):
    time_str = ''
    for match in matches:
        time_str = match.group()
    minute, sec = time_str.split(' ')
    minute = int(minute[:-1])
    sec = int(sec[:-1])
    return (minute*60) + sec

def accumulate_card_time(cards):
    pattern = '[0-9]{1,4}m [0-9]{1,2}s'
    times = 0
    for card in cards:
        title = card['name']
        matches = list(re.finditer(pattern, title))
        times += smart_time(matches)

    return times

def get_times_and_labels(cards):
    pattern = '[0-9]{1,4}m [0-9]{1,2}s'
    data = []
    for card in cards:
        matches = list(re.finditer(pattern, card['name']))
        if matches:
            s,e = matches[0].span()
            data += [(card['name'][:s], smart_time(matches))]
        else:
            

    data = sorted(data, key=lambda a: a[1])
    return data


def detect_green():
    # detect index of current card, and subtract times
    pass

def generate_title_summary(serial_cards, begin_time):
    title_1 = 'Projected end time: {}'
    title_2 = 'Total minutes: {}'
    total_time = accumulate_card_time(serial_cards)
    end_time = begin_time + datetime.timedelta(seconds=total_time)
    return ' ||| '.join((title_1.format(end_time.time().strftime('%H:%M:%S %M')),
                title_2.format(str(total_time//60) + ' minutes')))



def order_changed(serial_cards, new_cards):
    # titles = tuple(map(lambda a: [x['name'] for x in a], (serial_cards, new_cards)))
    ids = tuple(map(lambda a: [x['id'] for x in a], (serial_cards, new_cards)))
    return ids[0] != ids[1]


def main(stats_card, q):
    timer_id = '5610133e828fdc95eded90a5'
    serial_list_id = '5610135234343b361fb9b094'

    today = datetime.date.today().isoformat()

    api_key = os.environ['TRELLO_APIKEY']
    token = os.environ['TRELLO_TOKEN']

    trello = trello_api.TrelloApi(api_key, token)
    boards = login_and_get_boards(trello)

    lists = get_lists(trello, timer_id)
    stats_id = filter_lists(lists, 'Stats')
    original_stats_card_name = stats_card['name']
    piechart_card = trello.cards.new('Task time overview for {}'.format(today), stats_id)
    serial_cards = []
    begin_time = datetime.datetime.now()

    while True:
        if not q.empty():
            if q.get():
                q.task_done()
                print('Quitting')
                break
        new_cards = get_cards(trello, serial_list_id)
        if order_changed(serial_cards, new_cards):
            serial_cards = new_cards
            title = generate_title_summary(serial_cards, begin_time)
            data = get_times_and_labels(serial_cards)
            labels = list(map(lambda a: a[0], data))
            times = list(map(lambda a: a[1], data))
            link = plt_data.draw_piechart(labels, times)
            trello.cards.new_attachment(piechart_card['id'], link, 'Chart')
            trello.cards.update_name(stats_card['id'], title)

        time.sleep(5)
