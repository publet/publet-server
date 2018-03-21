from datetime import datetime
from urlparse import urlparse

from publet.utils.fn import flatten, get_in, ip2int
from publet.utils.utils import user_agent_to_device
from models import Event, get_location_for_ip_int


SOCIAL_SOURCES = ['twitter', 'facebook', 'linkedin', 'googleplus']


def get_event_type(data, event_name):
    for name, obj in data:
        if name == event_name:
            yield obj


def datetime_to_epoch(dt):
    delta = dt - datetime(1970, 1, 1)
    return int(delta.total_seconds() * 1000)


def parse_js_timestamp(t):
    return datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ')


def parse_raw_data(payload):
    if not payload:
        return None

    data = payload['data']
    ip = ip2int(payload['ip'])
    context = get_context(data, ip)

    return flatten([
        parse_page_data(context, data),
        parse_action_data(context, data),
        parse_read_data(context, data),
        parse_engaged_data(context, data),
        parse_engaged_article_data(context, data),
        parse_engaged_block_data(context, data)
    ])


def save_events(events):
    return Event.objects.bulk_create(events)


def get_social_source_by_referrer(referrer):
    values = {
        't.co': 'twitter',
        'www.facebook.com': 'facebook',
        'www.linkedin.com': 'linkedin',
        'lnkd.in': 'linkedin',
        'plus.google.com': 'googleplus'
    }

    domain = urlparse(referrer).netloc

    try:
        return values[domain]
    except KeyError:
        return ''


def get_context(data, ip):
    identity = [v['obj'] for k, v in data if k == 'identify'][0]
    pages = [v['obj'] for k, v in data if k == 'page']

    user_id = identity['userId']
    anonymous_id = identity['anonymousId']

    referrer = pages[0]['properties']['referrer'] or ''
    publication_id = pages[0]['properties'].get('publication', None)
    block_id = pages[0]['properties'].get('block', None)
    ts = pages[0].get('timestamp', None)

    location = get_location_for_ip_int(ip)

    user_agent = get_in(identity, 'traits', 'agent')
    languages = get_in(identity, 'traits', 'languages')

    if languages:
        languages = '|'.join(languages)

    social = [v['obj']['event'] for k, v in data
              if k == 'track' and v['obj']['event'] in SOCIAL_SOURCES]

    if social:
        social_source = social[0]
    else:
        social_source = get_social_source_by_referrer(referrer)

    device = user_agent_to_device(user_agent)

    return {
        'user_id': user_id,
        'referrer': referrer,
        'ip': ip,
        'location': location,
        'publication_id': publication_id,
        'block_id': block_id,
        'anonymous_id': anonymous_id,
        'social_source': social_source,
        'user_agent': user_agent,
        'languages': languages,
        'device': device,
        'ts': ts
    }


def parse_page_data(c, data):
    pages = []

    for name, obj in data:
        if name == 'page':
            pages.append(obj['obj'])

    events = []

    for p in pages:
        ts = parse_js_timestamp(p['timestamp'])
        events.append(
            Event(type='page', created=ts, user_id=c['user_id'], ip=c['ip'],
                  anonymous_id=c['anonymous_id'],
                  url=p['properties']['url'], referrer=c['referrer'],
                  publication_id=c['publication_id'], block_id=c['block_id'],
                  social_referrer=c['social_source'],
                  user_agent=c['user_agent'], languages=c['languages'],
                  continent=c['location']['continent'],
                  country=c['location']['country'],
                  region=c['location']['region'],
                  device=c['device'],
                  city=c['location']['city']))
    return events


def parse_action_data(c, data):
    actions = []

    for name, obj in data:
        if name == 'track':
            if obj['obj']['event'] == 'action':
                actions.append(obj['obj'])

    events = []

    for a in actions:
        ts = parse_js_timestamp(a['timestamp'])
        events.append(
            Event(type='action', created=ts, user_id=c['user_id'], ip=c['ip'],
                  action_type=a['properties']['type'],
                  action_name=a['properties']['name'],
                  action_value=a['properties']['value'],
                  anonymous_id=c['anonymous_id'],
                  referrer=c['referrer'],
                  publication_id=c['publication_id'], block_id=c['block_id'],
                  social_referrer=c['social_source'],
                  user_agent=c['user_agent'], languages=c['languages'],
                  continent=c['location']['continent'],
                  country=c['location']['country'],
                  region=c['location']['region'],
                  device=c['device'],
                  city=c['location']['city']))
    return events


def parse_read_data(c, data):
    read_tracks = get_event_type(data, 'read')
    events = []

    for t in read_tracks:
        events.append(
            Event(type='read_publication', created=c['ts'],
                  user_id=c['user_id'], ip=c['ip'],
                  anonymous_id=c['anonymous_id'],
                  publication_id=t['publication'],
                  percent_read=t['value'],
                  referrer=c['referrer'], social_referrer=c['social_source'],
                  user_agent=c['user_agent'], languages=c['languages'],
                  continent=c['location']['continent'],
                  country=c['location']['country'],
                  region=c['location']['region'],
                  device=c['device'],
                  city=c['location']['city']))

    # Articles read
    read_tracks = get_event_type(data, 'articles-read')

    for t in read_tracks:
        articles = t['value']

        for a in articles:
            events.append(
                Event(type='read_article', created=c['ts'],
                      user_id=c['user_id'], ip=c['ip'],
                      anonymous_id=c['anonymous_id'],
                      article_id=a['articleId'],
                      publication_id=t['publication'],
                      percent_read=a['percentRead'], referrer=c['referrer'],
                      social_referrer=c['social_source'],
                      user_agent=c['user_agent'], languages=c['languages'],
                      continent=c['location']['continent'],
                      country=c['location']['country'],
                      region=c['location']['region'],
                      device=c['device'],
                      city=c['location']['city']))

    return events


def parse_engaged_data(c, data):
    engaged_tracks = get_event_type(data, 'engaged')
    events = []

    for t in engaged_tracks:
        events.append(
            Event(type='engaged_publication', created=c['ts'],
                  user_id=c['user_id'], ip=c['ip'],
                  anonymous_id=c['anonymous_id'],
                  publication_id=int(t['publication']),
                  seconds=t['seconds'], referrer=c['referrer'],
                  social_referrer=c['social_source'],
                  user_agent=c['user_agent'], languages=c['languages'],
                  continent=c['location']['continent'],
                  country=c['location']['country'],
                  region=c['location']['region'],
                  device=c['device'],
                  city=c['location']['city']))

    return events


def parse_engaged_article_data(c, data):
    engaged_tracks = [v['obj'] for k, v in data
                      if k == 'track' and v['obj']['event'] == 'engaged']

    events = []

    for t in engaged_tracks:
        ts = parse_js_timestamp(t['timestamp'])
        for article_id, secs in t['properties']['articleSeconds'].items():
            article_id = int(article_id)
            events.append(
                Event(type='engaged_article', created=ts,
                      user_id=c['user_id'], ip=c['ip'],
                      anonymous_id=c['anonymous_id'],
                      article_id=article_id, seconds=secs,
                      publication_id=t['properties']['publication'],
                      referrer=c['referrer'],
                      social_referrer=c['social_source'],
                      user_agent=c['user_agent'], languages=c['languages'],
                      continent=c['location']['continent'],
                      country=c['location']['country'],
                      region=c['location']['region'],
                      device=c['device'],
                      city=c['location']['city']))

    return events


def parse_engaged_block_data(c, data):
    engaged_tracks = get_event_type(data, 'engaged')

    events = []

    for t in engaged_tracks:
        for block_id, secs in t['blockSeconds'].items():
            block_id = int(block_id)
            events.append(
                Event(type='engaged_block', created=c['ts'],
                      user_id=c['user_id'], ip=c['ip'],
                      anonymous_id=c['anonymous_id'], block_id=block_id,
                      seconds=secs, publication_id=t['publication'],
                      referrer=c['referrer'],
                      social_referrer=c['social_source'],
                      user_agent=c['user_agent'], languages=c['languages'],
                      continent=c['location']['continent'],
                      country=c['location']['country'],
                      region=c['location']['region'],
                      device=c['device'],
                      city=c['location']['city']))

    return events


def get_mean_engaged_time(publication_id):
    e = Event.objects.daily_average_publication_engaged_time(publication_id)
    return [int(v) for t, v in e]


def get_mean_engaged_article_time(article_id):
    e = Event.objects.daily_average_article_engaged_time(article_id)
    return [int(v) for t, v in e]


def get_mean_engaged_data(publication):
    articles = {}

    for article in publication.get_articles():
        articles[article.pk] = {
            'value': Event.objects.article_engaged_time(article.pk),
            'name': article.name
        }

    return {
        'publication': get_mean_engaged_time(publication.pk),
        'articles': dict(articles)
    }


def get_social_data(publication_id):
    return dict(Event.objects.get_social_data(publication_id))


def get_social_data_per_block(publication_id):
    return Event.objects.get_social_data_per_block(publication_id)
