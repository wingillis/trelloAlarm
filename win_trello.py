
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
        time, tstr = parseTime(time)
        return (name, time, tstr, title)
    except:
        return tuple([None]*4)

def parseProcessedCard(card):
    title = card['name']
    output = {
        '1.name': '',
        '2.date': '',
        '3.original time': '',
        '4.actual time', ''
    }
    try:
        name, rest = title.split('-')
        if '|||' in rest:
            ot, at = rest.split('|||')
            at = at.replace(' actual time ', '')

        else:
            ot = rest
            at = rest
        name = name.strip()
        # original timing
        ot = ot.strip()
        ott, _ = parseTime(ot)
        # actual timing
        at = at.strip()
        att, _ = parseTime(at)

        output['1.name'] = name
        output['2.date'] = card['dateLastActivity']
        output['3.original time'] = ott
        output['4.actual time'] = att
        return output
    except Exception as e:
        return {'error': str(e)}





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
