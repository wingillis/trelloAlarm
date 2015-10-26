import re
from collections import defaultdict

def login_and_get_boards(trello):
    wg = trello.members.get('winthropgillis')
    boards = wg['idBoards']
    return boards

def get_cards(trello, c_id):
    cards = trello.lists.get_card(c_id)
    return cards

def get_lists(trello, b_id):
    lists = trello.boards.get_list(b_id)
    return lists

def filter_lists(lists, l_name):
    return [x['id'] for x in lists if x['name'] == l_name][0]

def filter_board(trello, b, name):
    board = trello.boards.get(b)
    return board['name'] == name

def get_board(trello, boards, board):
    return [x for x in boards if filter_board(trello, x, board)][0]

def parseCard(card):
    title = card['name']
    try:
        name, time = title.split('-')
        name = name.strip()
        time = time.strip()
        time, tstr = parseTime(time, True)
        return (name, time, tstr, title)
    except:
        return tuple([None]*4)

def parseProcessedCard(card):
    title = card['name']
    pattern = '[0-9]{1,4}m [0-9]{1,2}s'
    output = {
        '1.name': '',
        '2.date': '',
        '3.original time': '',
        '4.actual time': ''
    }
    try:
        matches = list(re.finditer(pattern, title))
        if len(matches) == 0 or len(matches) > 2:
            raise Exception('Error in matches found - timing information not available')

        s,e = matches[0].span()
        name = title[:s-3]
        ot = title[s:e]
        if len(matches) > 1:
            s,e = matches[1].span()
            at = title[s:e]
        else:
            at = title[s:e]
        name = name.strip()
        # original timing
        ott = parseTime(ot)
        # actual timing
        att = parseTime(at)

        output['1.name'] = name
        output['2.date'] = card['dateLastActivity']
        output['3.original time'] = str(ott)
        output['4.actual time'] = str(att)
        return output
    except Exception as e:
        return {'error': str(e)}

def parseTime(tstr, human_readable=False):
    sminute, ssec = tstr.split(' ')
    minute = int(sminute[:-1])
    sec = int(ssec[:-1])
    if human_readable:
        time_str = ''
        if minute:
            time_str += '{} minutes '.format(minute)
        if sec:
            if time_str:
                time_str += 'and '
            time_str += '{} seconds'.format(sec)
        return (sec+ minute*60, time_str)
    else:
        return sec + minute * 60

def find_yellow(cards):
    yellow_cards = [i for i, x in enumerate(cards) for y in x['labels'] if 'yellow' in y['color']]
    if yellow_cards:
        return yellow_cards[0] + 1
    else:
        return 0

def generate_card(trello, l_id, title):
    card = trello.cards.new(title, l_id)
    return card

def get_tags(cards):
    titles = [card['name'] for card in cards]
    pattern = '#(?P<tag>\w+) '
    data = defaultdict(list)
    for name in titles:
        tags = list(re.finditer(pattern, name))
        for t in tags:
            data[t.group('tag')] += [name]
    return data

def filter_for_tag(cards, tag):
    ''' returns a list of cards with that tag if the tag exists,
    else it returns None'''
    tags = get_tags(cards)
    cs = tags.get(tag, None)
    if cs:
        return [c for c in cards if c['name'] in cs]
    else:
        return None
