
# coding: utf-8

# In[1]:

import trello
import pync
import time
import subprocess
import os


# In[2]:

api_key = os.environ['TRELLO_APIKEY']
token = os.environ['TRELLO_TOKEN']


# In[3]:

t = trello.TrelloApi(api_key, token=token)


# In[4]:

def login_and_get_boards(trello):
    wg = trello.members.get('winthropgillis')
    boards = wg['idBoards']
    return boards


# In[5]:

boards = login_and_get_boards(t)


# In[6]:

def filter_board(trello, b, name):
    board = trello.boards.get(b)
    return board['name'] == name

def get_board(trello, boards, board):
    return [x for x in boards if filter_board(trello, x, board)][0]


# In[7]:

timer_board_id = get_board(t, boards, 'Timers')


# In[8]:

def get_lists(trello, b_id):
    lists = trello.boards.get_list(b_id)
    return lists

def get_cards(trello, c_id):
    cards = trello.lists.get_card(c_id)
    return cards


# In[9]:

lists = get_lists(t, timer_board_id)


# In[10]:

serial = list(filter(lambda d: d['name'] == 'Serial', lists))[0]
parallel = list(filter(lambda d: d['name'] == 'Parallel', lists))[0]


# In[11]:

ser_cards = get_cards(t, serial['id'])


# In[12]:

def parseCard(card):
    title = card['name']
    name, time = title.split('-')
    name = name.strip()
    time = time.strip()
    time, tstr = parseTime(time)
    return (name, time, tstr, title)

def parseTime(tstr):
    sminute, ssec = tstr.split(' ')
    minute = int(sminute[:-1])
    sec = int(ssec[:-1])
    time_str = ''
    if minute:
        time_str += '{} minutes '.format(minute)
    if sec:
        if time_str:
            time_str += 'and '
        time_str += '{} seconds'.format(sec)
    return (sec+ minute*60, time_str)    


# In[13]:

def run_serial_timer(trello, cards, loud=True):
    l = len(cards)
    future, t, tstr, _t = parseCard(cards[0])
    subprocess.call(['say', 'Do {} for {}'.format(future, tstr)])
    for i, card in enumerate(cards):
        if i<l-1:
            future, t, tstr, _t = parseCard(cards[i+1])
        else:
            future = None
        name, t, ttemp, title = parseCard(card)
        trello.cards.new_label(card['id'], 'green')
        minute = t//60
        sec = t%60
        if minute:
            for j in range(minute,0,-1):
                trello.cards.update_name(card['id'], '{} ends in {}'.format(name, str(j) + ' minutes'))
                time.sleep(60)
        if sec:
            trello.cards.update_name(card['id'], '{} ends in {}'.format(name, str(sec) + ' seconds'))
            time.sleep(sec)
        pync.Notifier.notify(name, title='Timer Up!')
        if loud:
            subprocess.call(['afplay', 'gong trim.m4a', '-t', '1'])
        if future and loud:
            subprocess.call(['say', '{} is over. Now do {} for {}'.format(name, future, tstr)])
        elif loud:
            subprocess.call(['say', '{} is over'.format(name)])
        trello.cards.delete_label_color('green', card['id'])
        trello.cards.update_name(card['id'], title)


# In[15]:

run_serial_timer(t, ser_cards)


# In[15]:

def repeat():
    ser_cards = get_cards(t, serial['id'])
    run_serial_timer(t, ser_cards)
    
def repeat_quiet():
    ser_cards = get_cards(t, serial['id'])
    run_serial_timer(t, ser_cards, False)


# In[16]:

# TODO
# Add label to current timer and add to title how long it has left
repeat_quiet()


# In[ ]:



