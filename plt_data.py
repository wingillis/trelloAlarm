import matplotlib.pyplot as plt
import seaborn as sns
from os import environ as env
from os import remove
import datetime
import hashlib
from imgurpython import ImgurClient

client = ImgurClient(env['IMGUR_ID'], env['IMGUR_SECRET'], env['imgur_access'], env['imgur_refresh'])

def upload_image(title):
    res = client.upload_from_path(title, {'title':title})
    return res

def draw_piechart(labels, times):
    name = hashlib.sha224(datetime.datetime.now()
                .isoformat().encode('utf-8')).hexdigest() + '.png'

    plt.pie(times, labels=labels)

    plt.axis('equal')

    plt.savefig(name)

    link = upload_image(name)

    remove(name)

    return link['link']
