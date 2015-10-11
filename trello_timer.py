#!/Users/wgillis/anaconda/bin/python
import trello as trello_api
import time
import subprocess
import os
import datetime
import sys
from win_trello import *


def say(text):
    subprocess.call(['say', text])

def find_card_in_list(lis, card):
    pos = [i for i,x in enumerate(lis) if x['id']==card['id']][0]
    return pos

def compare(list1, list2):
    list1_ids = [a['id'] for a in list1]
    list2_ids = [a['id'] for a in list2]
    return list1_ids == list2_ids

def is_done(card):
    for label in card['labels']:
        if label['name'] == 'Done':
            return True
    return False

def not_done(card):
    for label in card['labels']:
        if label['name'] == 'Not Done':
            return True
    return False

def main_timer(trello, cards, index, serial_id, loud=True):
    def new_name(card, s):
        trello.cards.update_name(card['id'], s)
    def timer_name(card, name, t, seconds=False, added=None):
        s = '{} ends in {}'
        s += ' seconds' if seconds else ' minutes'
        if added:
            s += added
        new_name(card, s.format(name, t))

    do = 'Do {} for {}'
    over = '{} is over. Now do {} for {}'
    enumerate_cards = cards[index:]
    l = len(enumerate_cards) # for saying next card
    compare_cards = []
    card_stats = {}
    end = False

    for i, card in enumerate(enumerate_cards):
        # get information for the next task, if there is one
        if i<l-1:
            future, t, tstr, _t = parseCard(enumerate_cards[i+1])
        else:
            future = None
        name, t, ttemp, title = parseCard(card)

        # say the first task
        if i==0 and l!=1:
            say(do.format(name, ttemp))

        # add 'current' label
        trello.cards.new_label(card['id'], 'green')

        t, remainder = t//10 * 10 , t%10
        minutes = t//60
        plus_time = 0

        # one-time update
        if minutes:
            timer_name(card, name, minutes)

        for i in range(t, 0, -10):
            # get labels for current card
            if sys.stdin.readline().strip() == 'end':
                end = True
                break
            card = trello.cards.update(card['id'])
            if is_done(card):
                delta = t-(i+remainder)
                # record delta in card's title - override title because of bottom
                title += ' ||| actual time {}m {}s'.format(delta//60, delta%60)
                remainder = 0
                break
            if not_done(card):
                while not_done(card):
                    time.sleep(10)
                    plus_time += 10
                    card = trello.cards.update(card['id'])
                    if is_done(card):
                        break
                    if plus_time%60 == 0:
                        val, sec = i + remainder if not minutes else i//60, (not minutes)
                        timer_name(card, name, val, sec,
                                added=' running for an additional {}m {}s'
                                    .format(plus_time//60, plus_time%60))
                delta = i + plus_time
                title += ' ||| actual time {}m {}s'.format(delta//60, delta%60)
                break

            if not minutes:
                timer_name(card, name, i + remainder, True)

            elif minutes != i//60:
                minutes = i//60
                timer_name(card, name, minutes)

            time.sleep(10)


        # finish the rest of the seconds on the timer
        if remainder and not end:
            time.sleep(remainder)

        # if loud:
        #     # plays the desired sound on a mac for 1s
        #     subprocess.call(['afplay', 'gong trim.m4a', '-t', '1'])

        trello.cards.delete_label_color('green', card['id'])
        new_name(card, title)

        if end:
            trello.cards.new_label(card['id'], 'yellow')
            return (False, None, None)

        # detect new cards, then compare them to see if they are different
        # if so, then look for the specific card in the new list, and return
        # that index plus 1
        compare_cards = get_cards(trello, serial_id)

        if not compare(compare_cards, cards):
            point = find_card_in_list(compare_cards, card)
            return (True, compare_cards, point+1)

        if future and loud:
            say(over.format(name, future, tstr))
        elif loud:
            say('{} is over'.format(name))


    return (False, None, None)


# every 10 seconds, detect label on card

def main():
    api_key = os.environ['TRELLO_APIKEY']
    token = os.environ['TRELLO_TOKEN']

    trello = trello_api.TrelloApi(api_key, token)
    boards = login_and_get_boards(trello)
    # gathered from previous tests, assuming they don't change
    timer_id = '5610133e828fdc95eded90a5'
    serial_list_id = '5610135234343b361fb9b094'

    # if the ids do change, use this
    # timer_id = get_board(trello, boards, 'Timers')
    # lists = get_lists(trello, timer_id)
    # serial_list = list(filter(lambda d: d['name'] == 'Serial', lists))[0]
    # serial_list_id = serial_list['id']

    cards = get_cards(trello, serial_list_id)
    run = True
    index = 0

    while run:
        run, cards, index = main_timer(trello, cards, index, serial_list_id)
        if run:
            print('New card added, restarting timer')

    print('Nice!')

if __name__=='__main__':
    main()
