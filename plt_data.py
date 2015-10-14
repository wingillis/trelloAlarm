from os import environ as env
from os import remove
import datetime
import hashlib
from imgurpython import ImgurClient
import boto3
import plotly.plotly as plt
import plotly.graph_objs as gph
import plotly.tools as tls

client = ImgurClient(env['IMGUR_ID'], env['IMGUR_SECRET'], env['imgur_access'], env['imgur_refresh'])
s3 = boto3.resource('s3')

def upload_image(title):
    res = client.upload_from_path(title, {'title':title})
    return res

def draw_piechart(labels, times):
    name = hashlib.sha224(datetime.datetime.now()
                .isoformat().encode('utf-8')).hexdigest() + '.png'

    data = {
        'data': [{
            'labels': labels,
            'values': times,
            'type': 'pie',
        }],
        'layout': {
            'title': 'Proportion of time for each task',
            # 'legend': gph.Legend(font=gph.Font(size=20))
        }
    }

    plt.image.save_as(data, name, width=1280, height=760)
    url = plt.plot(data, validate=False, filename=datetime.date.today().isoformat() + ' Trello task history', auto_open=False)
    embed = tls.get_embed(url)
    s3.Bucket('wg-plots').put_object(Key=datetime.date.today().isoformat(), Body=embed, ContentType='text/html')
    url = 'https://s3.amazonaws.com/wg-plots/{}.html'.format(datetime.date.today.isoformat())
    link = upload_image(name)

    remove(name)

    return (link['link'], url)
