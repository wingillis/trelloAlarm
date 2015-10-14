import trello as trello_api
from win_trello import *
import os
import time
import datetime
import re
import plt_data
# from io import StringIO

# add all new cards to 'original' sub-dictionary
# add all modifications to 'modified' sub-dictionary
# card_data {}
#
# def update_card_data(cards):
#     global card_data
#     for card in cards:
#         if card['id'] not in card_data:
#             card_data[card['id']] = {}
#             card_data[card['id']]['original'] = card
#         else:
#             card_data[card['id']]['modified'] = card
#     # remove any cards not in card data
#     card_ids = set(card_data.keys())
#     new_ids = set([card['id'] for card in cards])
#     for i in card_ids - new_ids:
#         del card_data[i]


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
        if is_current_timer(card):
            title = card['desc']
        matches = list(re.finditer(pattern, title))
        times += smart_time(matches)

    return times

def is_current_timer(card):
    labels = card['labels']
    if not labels:
        return False
    green = list(filter(lambda a: a['color'] == 'green', labels))
    if green:
        return True
    else:
        return False

def get_times_and_labels(cards):
    pattern = '[0-9]{1,4}m [0-9]{1,2}s'
    data = []
    for card in cards:
        title = card['name']
        if is_current_timer(card):
            matches = list(re.finditer(pattern, card['desc']))
            title = card['desc']
        else:
            matches = list(re.finditer(pattern, card['name']))
        data += [(title, smart_time(matches))]

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
    return ' ||| '.join((title_1.format(end_time.time().strftime('%H:%M:%S')),
                title_2.format(str(total_time//60) + ' minutes')))



def order_changed(serial_cards, new_cards):
    # only change for differences in descriptions or ids
    ids = tuple(map(lambda a: [x['id'] for x in a], (serial_cards, new_cards)))
    return (ids[0] != ids[1])

def something_changed(serial_cards, new_cards):

    desc = list(map(lambda a: [x['desc'] for x in a], (serial_cards, new_cards)))
    title = list(map(lambda a: [x['name'] for x in a if not is_current_timer(x)], (serial_cards, new_cards)))
    c1 = set(desc[0]) | set(title[0])
    c2 = set(desc[1]) | set(title[1])
    return c1 != c2


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
    piechart_card = trello.cards.new('Task time overview for {}'.format(today), stats_id)
    cards = get_cards(trello, stats_id)
    trello.cards.update(piechart_card['id'], pos=(cards[0]['pos']+cards[1]['pos'])/2)
    serial_cards = []
    begin_time = datetime.datetime.now()

    while True:
        if not q.empty():
            if q.get():
                q.task_done()
                print('Quitting')
                trello.cards.update(piechart_card['id'], pos=piechart_card['pos']+1)
                break
        try:
            new_cards = get_cards(trello, serial_list_id)
       	    if order_changed(serial_cards, new_cards) or something_changed(serial_cards, new_cards):
                serial_cards = new_cards
                # update_card_data(serial_cards)
                title = generate_title_summary(serial_cards, begin_time)
                trello.cards.update_name(stats_card['id'], title)

                data = get_times_and_labels(serial_cards)
                labels = list(map(lambda a: a[0], data))
                times = list(map(lambda a: a[1], data))
                img_link, plotly_link = plt_data.draw_piechart(labels, times)
                if piechart_card['badges']['attachments'] >= 2:
                    for a in trello.cards.get_attachment(piechart_card['id']):
                        trello.cards.delete_attachment(piechart_card['id'], a['id'])
                trello.cards.new_attachment(piechart_card['id'], img_link, 'Chart')
                # f = StringIO(plotly_link)
                trello.cards.new_attachment(piechart_card['id'], plotly_link, 'Chart - Interactive')

                piechart_card = trello.cards.update(piechart_card['id'])
        except Exception as e:
            print('Catching exception that was thrown... {}'.format(e))
            print('Don\'t worry, not stopping the program')



        time.sleep(10)
