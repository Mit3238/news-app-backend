from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import feedparser
from datetime import datetime, timedelta
import pytz
from gtts import gTTS
import os

app = Flask(__name__)
CORS(app)

# save all data in catorgories folders like india, international, Economy, Markets

rss = {"india":"https://www.thehindu.com/news/national/feeder/default.rss",
       "world":"https://www.thehindu.com/news/international/feeder/default.rss",
       "Economy":"https://www.thehindu.com/business/Economy/feeder/default.rss",
       "Markets":"https://www.thehindu.com/business/markets/feeder/default.rss"}

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Hello, World!'})

@app.route('/total-feeds', methods=['GET'])
def total_feeds():
    return jsonify({"rss":list(rss.keys())})

@app.route('/news', methods=['GET'])
def news():
    rss_url = "https://www.thehindu.com/news/international/feeder/default.rss"  

    feed = feedparser.parse(rss_url)

    if feed.bozo:  # Check for potential errors
        raise Exception("Error parsing RSS feed")

    feed_data = {
        'title': feed.feed.get('title', ''),
        'link': feed.feed.get('link', ''),
        'description': feed.feed.get('description', ''),
        'entries': []
    }

    for entry in feed.entries:
        feed_data['entries'].append({
            'title': entry.get('title', ''),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', '') 
        })

    all_text = ""

    yesterday = datetime.now() - timedelta(days=1)

    for i in range(0, len(feed_data['entries'])):
        date = datetime.strptime(feed_data['entries'][i]['published'], "%a, %d %b %Y %H:%M:%S %z")
        date = date.replace(tzinfo=None)
        if date > yesterday:
            all_text += feed_data['entries'][i]['title'] + ".\n"
            if feed_data['entries'][i]['summary'] != '':
                all_text += "\t" + feed_data['entries'][i]['summary'] + ".\n"

    print(len(all_text))

    tts = gTTS(text=all_text, lang='en')  
    tts.save(f'{datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")}.mp3')

    return jsonify(feed_data)

@app.route('/news-refresh', methods=['GET'])
def news_refresh():
    rss_url = "https://www.thehindu.com/news/international/feeder/default.rss"  

    feed = feedparser.parse(rss_url)

    if feed.bozo:  # Check for potential errors
        raise Exception("Error parsing RSS feed")

    feed_data = {
        'title': feed.feed.get('title', ''),
        'link': feed.feed.get('link', ''),
        'description': feed.feed.get('description', ''),
        'entries': []
    }

    for entry in feed.entries:
        feed_data['entries'].append({
            'title': entry.get('title', ''),
            'link': entry.get('link', ''),
            'published': entry.get('published', ''),
            'summary': entry.get('summary', '') 
        })

    yesterday = datetime.now() - timedelta(days=1)

    new = 0
    for i in range(0, len(feed_data['entries'])):
        date = datetime.strptime(feed_data['entries'][i]['published'], "%a, %d %b %Y %H:%M:%S %z")
        date = date.replace(tzinfo=None)
        if date > yesterday:
            file_name = f'{datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")}'
            if file_name + '.txt' not in os.listdir('data/news'):
                txt = ''
                new += 1
                print(new)
                with open(f'data/news/{file_name}.txt', 'w') as f:
                    f.write(feed_data['entries'][i]['title'] + "\n")
                    txt += feed_data['entries'][i]['title'] + "\n"
                    if feed_data['entries'][i]['summary'] != '':
                        f.write(feed_data['entries'][i]['summary'] + "\n")
                        txt += feed_data['entries'][i]['summary'] + "\n"
                tts = gTTS(text=txt, lang='en')
                tts.save(f'data/news/audio/{file_name}.mp3')

    return jsonify({'new': new})

@app.route('/news-list', methods=['GET'])
def news_list():
    return jsonify(os.listdir('data/news'))

@app.route('/news-send/<name>/<start>/<end>', methods=['GET'])
def news_send(name, start, end):
    print(name)
    end = int(end)
    start = int(start)
    files = os.listdir('data/news')
    files.remove('audio')
    files.sort(reverse=True)
    files = files[start:end]

    for i in range(len(files)):
        files[i] = files[i].split('.')[0]

    res = {'files': files, 'data':{}}
    for file in files:
        with open(f'data/news/{file}.txt', 'r') as f:
            res['data'][file] = f.read()

    return jsonify(res)

# send audio file to the client
@app.route('/news-audio/<name>/<date>', methods=['GET'])
def news_audio(name, date):
    print(name)
    return send_file(f'data/news/audio/{date}.mp3')

if __name__ == '__main__':
    app.run(debug=True)
