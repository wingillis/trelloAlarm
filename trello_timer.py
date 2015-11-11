#!/Users/wgillis/anaconda/bin/python
import trello as trello_api
import time
import subprocess
import os
import datetime
import sys
import select
import threading
import trello_stats
import queue
import pushbullet
from win_trello import *
from win_pushbullet import *

pb = pushbullet.Pushbullet(os.environ['pushbullet_token'])
devs = [x for x in pb.devices
            if x.nickname in ('AndroidPhone', 'Python app')]
comp = [x for x in devs if 'Python' in x.nickname][0]
android = [x for x in devs if 'Android' in x.nickname][0]

def say(text):
    android.push_note('Trello timer', text)
    subprocess.call(['say', text])
    # pass

def poll():
    # get messages sent to comp and then parse them
    # TODO: Get and parse messages and return state a value
    notifs = pb.get_pushes(limit=4)
    
    pass

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

def is_ending():
    ready = select.select([sys.stdin], [], [], 0)[0]
    if ready and sys.stdin.readline().strip() == 'end':
        return True
    else:
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
        try:
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
            trello.cards.update_desc(card['id'], title)
            # one-time update
            if minutes:
                timer_name(card, name, minutes)

            for j in range(t, 0, -10):
                # check for ending

                if is_ending():
                    end = True
                    break
                t1 = time.time()
                card = trello.cards.update(card['id'])
                if is_done(card):
                    print('Card finished early')
                    delta = t-(j+remainder)
                    # record delta in card's title - override title because of bottom
                    title += ' actual time {}m {}s'.format(delta//60, delta%60)
                    remainder = 0
                    break
                if not_done(card):
                    print('Card detected to be not done')
                    while not_done(card):
                        tt1 = time.time()
                        if is_ending():
                            print('Ending detected! Shutting down...')
                            trello.cards.delete_label_color('orange', card['id'])
                            end = True
                            break
                        card = trello.cards.update(card['id'])

                        if is_done(card):
                            print('Delayed card now finished')
                            break
                        if plus_time%60 == 0:
                            val, sec = j + remainder if (not minutes and j<60) else j//60, (not minutes and j<60)
                            delta = t - (j + remainder) + plus_time
                            timer_name(card, name, val, sec,
                                    added=' delayed - running total {}m {}s'
                                        .format(delta//60, delta%60))
                        tt2 = time.time()
                        slpt = (10- (tt2-tt1))
                        if slpt<0:
                            slpt = 10
                        time.sleep(slpt)
                        plus_time += 10

                    if not end:
                        delta = t - (j + remainder) + plus_time
                        title += ' actual time {}m {}s'.format(delta//60, delta%60)
                        break

                # if end:
                #     print('End detected! Breaking out of timer loop')
                #     break

                if not minutes:
                    timer_name(card, name, j + remainder, True)

                elif minutes != round(j/60):
                    minutes = round(j/60)
                    timer_name(card, name, minutes)
                t2 = time.time()
                # print('This is how long it takes: {0:.2f}s'.format(t2-t1))
                slpt = 10 - (t2-t1)
                if slpt<0:
                    slpt = 10
                time.sleep(slpt)


            # finish the rest of the seconds on the timer
            if remainder and not end:
                time.sleep(remainder)

            # if loud:
            #     # plays the desired sound on a mac for 1s
            #     subprocess.call(['afplay', 'gong trim.m4a', '-t', '1'])

            trello.cards.delete_label_color('green', card['id'])
            trello.cards.update_desc(card['id'], '')
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
        except Exception as e:
            print('Error in main loop... {}'.format(e))
            new_name(card, title)
            return (True, cards, i)


    return (False, None, None)


# every 10 seconds, detect label on card

def main():
    q = queue.Queue()
    api_key = os.environ['TRELLO_APIKEY']
    token = os.environ['TRELLO_TOKEN']

    trello = trello_api.TrelloApi(api_key, token)
    boards = login_and_get_boards(trello)
    # gathered from previous tests, assuming they don't change
    timer_id = '5610133e828fdc95eded90a5'
    serial_list_id = '5610135234343b361fb9b094'

    # if the ids do change, use this
    # timer_id = get_board(trello, boards, 'Timers')
    lists = get_lists(trello, timer_id)
    stats_id = filter_lists(lists, 'Stats')
    stats_card = generate_card(trello, stats_id, 'Stats for {}'.format(datetime.date.today()))
    trello.cards.update(stats_card['id'], pos=0)
    thread = threading.Thread(target=trello_stats.main, args=(stats_card, q))
    thread.start()
    # serial_list = list(filter(lambda d: d['name'] == 'Serial', lists))[0]
    # serial_list_id = serial_list['id']

    cards = get_cards(trello, serial_list_id)
    run = True
    index = find_yellow(cards)


    if index:
        # I want to return a 'yes' even at the first element
        index -= 1
        trello.cards.delete_label_color('yellow', cards[index]['id'])


    while run:
        run, cards, index = main_timer(trello, cards, index, serial_list_id, loud=True)
        if run:
            print('New card added, restarting timer')

    trello.cards.update_closed(stats_card['id'], 'true')
    print('Nice!')
    q.put(True)
    q.join()

if __name__=='__main__':
    main()
