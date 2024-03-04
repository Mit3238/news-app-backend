from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import feedparser
from datetime import datetime, timedelta
from gtts import gTTS
import os

app = Flask(__name__)
CORS(app)

# save all data in catorgories folders like india, international, Economy, Markets

rss = {"india":"https://www.thehindu.com/news/national/feeder/default.rss",
       "world":"https://www.thehindu.com/news/international/feeder/default.rss",
       "Economy":"https://www.thehindu.com/business/Economy/feeder/default.rss",
       "Markets":"https://www.thehindu.com/business/markets/feeder/default.rss"}

os.makedirs('data', exist_ok=True)
for key in rss.keys():
    if key not in os.listdir('data'):
        os.mkdir(f'data/{key}')
    if 'audio' not in os.listdir(f'data/{key}'):
        os.mkdir(f'data/{key}/audio')

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Hello, from NEWS app!'})

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
    total = 0
    for key in rss.keys():
        rss_url = rss[key]
        # rss_url = "https://www.thehindu.com/news/international/feeder/default.rss"  

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

        last_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        files = os.listdir(f'data/{key}')
        files.remove('audio')
        for file in files:
            date = datetime.strptime(file.split('.')[0], "%Y-%m-%d-%H-%M-%S")
            if date < last_date:
                os.remove(f'data/{key}/{file}')
                os.remove(f'data/{key}/audio/{file}.mp3')

        yesterday = datetime.now() - timedelta(hours=48)

        new = 0
        for i in range(0, len(feed_data['entries'])):
            date = datetime.strptime(feed_data['entries'][i]['published'], "%a, %d %b %Y %H:%M:%S %z")
            date = date.replace(tzinfo=None)
            if date > yesterday:
                file_name = f'{datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")}'
                if file_name + '.txt' not in os.listdir(f'data/{key}'):
                    txt = ''
                    new += 1
                    total += 1
                    print(new)
                    with open(f'data/{key}/{file_name}.txt', 'w') as f:
                        f.write(feed_data['entries'][i]['title'] + "\n")
                        txt += feed_data['entries'][i]['title'] + "\n"
                        if feed_data['entries'][i]['summary'] != '':
                            f.write(feed_data['entries'][i]['summary'] + "\n")
                            txt += feed_data['entries'][i]['summary'] + "\n"
                    tts = gTTS(text=txt, lang='en')
                    tts.save(f'data/{key}/audio/{file_name}.mp3')

    return jsonify({'new': total})

@app.route('/news-list', methods=['GET'])
def news_list():
    return jsonify(os.listdir('data/news'))

@app.route('/news-send/<name>/<start>/<end>', methods=['GET'])
def news_send(name, start, end):
    print(name)
    end = int(end)
    start = int(start)
    files = os.listdir(f'data/{name}')
    files.remove('audio')
    files.sort(reverse=True)
    files = files[start:end]

    for i in range(len(files)):
        files[i] = files[i].split('.')[0]

    res = {'files': files, 'data':{}}
    for file in files:
        with open(f'data/{name}/{file}.txt', 'r') as f:
            res['data'][file] = f.read()

    return jsonify(res)

# send audio file to the client
@app.route('/news-audio/<name>/<date>', methods=['GET'])
def news_audio(name, date):
    print(name)
    return send_file(f'data/{name}/audio/{date}.mp3')

if __name__ == '__main__':
    app.run(debug=True)
