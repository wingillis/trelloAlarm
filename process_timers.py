import trello as trello_api
import os
from win_trello import *

def process_tasks(trello, plist):
    plist_cards = get_cards(trello, plist['id'])
    with open('task_history.csv', 'a') as f:
        for card in plist_cards:
            data = parseProcessedCard(card)
            if data.get('1.name', None):
                keys = sorted(list(data.keys()))
                line = ','.join([data[k] for k in keys])
                f.write(line + '\n')
                trello.cards.update_closed(card['id'], True)
            else:
                print(data.get('error', None))
                print('Card could not be parsed, keeping it')


def main():
    api_key = os.environ['TRELLO_APIKEY']
    token = os.environ['TRELLO_TOKEN']

    trello = trello_api.TrelloApi(api_key, token)
    boards = login_and_get_boards(trello)

    timer_id = get_board(trello, boards, 'Timers')

    lists = get_lists(trello, timer_id)

    process_list = list(filter(lambda d: d['name'] == 'For processing', lists))[0]
    process_tasks(trello, process_list)

if __name__=='__main__':
    main()
