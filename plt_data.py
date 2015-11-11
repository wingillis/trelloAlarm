from os import environ as env
from os import remove
import datetime
import hashlib
from imgurpython import ImgurClient
import boto3
import plotly.plotly as plt
import plotly.graph_objs as gph
import plotly.tools as tls
from itertools import accumulate
import requests

client = ImgurClient(env['IMGUR_ID'], env['IMGUR_SECRET'], env['imgur_access'], env['imgur_refresh'])
s3 = boto3.resource('s3')

def upload_image(title):
    res = client.upload_from_path(title, {'title':title})
    return res

def add_time(t1, tdelt):
    return t1 + datetime.timedelta(seconds=tdelt)

def rep_time(s):
    return s.strftime('%I:%M:%S %p')

def draw_horiz_bar_graph(data, begin_time):
    tickvals = list(accumulate(a[1] for a in data))
    ticklabels = [rep_time(add_time(begin_time, t)) for t in tickvals]
    traces = []
    # for (key, val) in data:
    #     traces += [gph.Bar(
    #         x=val,
    #         y=1,
    #         name=key,
    #         orientation='h'
    #         )]
    for (key, val) in data:
        traces += [{
            'x': val,
            'y': 1,
            'name': key,
            'orientation': 'h',
            'type': 'bar'
        }]

    # layout = gph.Layout(barmode='stack',
    #                    xaxis=dict(
    #                             tickvals=tickvals,
    #                             ticktext=ticklabels),
    #                     title= 'Time for finishing each task')
    # fig = gph.Figure(data=traces, layout=layout)
    layout = {
        'barmode': 'stack',
        'xaxis': {
            'tickvals': tickvals,
            'ticktext': ticklabels
        },
        'title': 'Time for finishing each task'
    }
    # return plotly_pipe(fig, 'hbar')
    return plotly_pipe({'data': traces, 'layout': layout}, 'hbar')

def draw_piechart(labels, times):
    data = {
        'data': [{
            'labels': labels,
            'values': times,
            'type': 'pie',
        }],
        'layout': {
            'title': 'Proportion of time for each task',
            # 'legend': gph.Legend(font=gph.Font(size=23))
        }
    }

    return plotly_pipe(data, 'pie')

def plotly_pipe(data, plt_type):
    name = hashlib.sha224(datetime.datetime.now()
                .isoformat().encode('utf-8')).hexdigest() + '.png'

    # plt.image.save_as(data, name, width=1280, height=760)
    url = plt.plot(data, validate=False, filename=datetime.date.today().isoformat() + ' Trello task history', auto_open=False)
    # print(url)
    composed_url = '{url}.{im}?width={w}&height={h}'.format(url=url, im='png', w=1280, h=760)
    with open(name, 'wb') as f:
        f.write(requests.get(composed_url).content)
    embed = tls.get_embed(url)
    s3.Bucket('wg-plots').put_object(Key=datetime.date.today().isoformat() + '-' + plt_type + '.html', Body=embed, ContentType='text/html')
    url = 'https://s3.amazonaws.com/wg-plots/{}-{}.html'.format(datetime.date.today().isoformat(), plt_type)
    link = upload_image(name)

    remove(name)

    return (link['link'], url)
