import json
import requests

from django.conf import settings
from django.template.loader import render_to_string

from publet.utils.s3 import upload_file_to_s3
from publet.utils.utils import purge_in_varnish
from publet.utils.metrics import Meter, Timer, time_as


HOST = getattr(settings, 'HOST', None)
REACT_BUILD_URL = getattr(settings, 'REACT_BUILD_URL', None)
ARTICLE_URL = REACT_BUILD_URL + '/api/article/'
AWS_BUCKET_PUBLICATIONS = getattr(settings, 'AWS_BUCKET_PUBLICATIONS')
TRACK_URL = getattr(settings, 'TRACK_URL', None)
TESTING = getattr(settings, 'TESTING', False)


@time_as('article.get_article_html')
def get_article_html(article):
    if TESTING:
        return

    Meter('article.build').inc()

    article = json.dumps(article)
    headers = {
        'Content-Type': 'application/json'
    }

    with Timer('article.build-time'):
        r = requests.post(ARTICLE_URL, data=article, headers=headers)

    if r.status_code != 200:
        Meter('article.build-failed').inc()
        raise Exception('react response was {}'.format(r.status_code))

    return r.json()


def parse_js_files(js):
    app = None
    deps = []

    for f in js:
        if 'app-' in f:
            app = f
        else:
            deps.append(f)

    return {
        'app': app,
        'deps': deps
    }


def get_article_document(instance, reactHTMLObj):
    return render_to_string('react.html', {
        'content': reactHTMLObj['reactHtml'],
        'css': reactHTMLObj['css'],
        'js': parse_js_files(reactHTMLObj['js']),
        'HOST': HOST,
        'track_url': TRACK_URL,
        'title': instance.publication.name,
        'publication': instance.publication,
        'article': instance,
        'fonts_url': instance.publication.new_theme.fonts_url
    })


def get_scroll_publication_document(publication, reactHTMLObjs):
    if not reactHTMLObjs:
        return

    articles_html = '\n\n'.join(map(lambda x: x['reactHtml'], reactHTMLObjs))
    css = reactHTMLObjs[0]['css']
    js = parse_js_files(reactHTMLObjs[0]['js'])

    return render_to_string('react.html', {
        'content': articles_html,
        'css': css,
        'js': js,
        'HOST': HOST,
        'track_url': TRACK_URL,
        'title': publication.name,
        'publication': publication,
        'fonts_url': publication.new_theme.fonts_url
    })


def upload_article_document(filename, article_document):
    if TESTING:
        return

    upload_file_to_s3(AWS_BUCKET_PUBLICATIONS,
                      article_document,
                      filename,
                      mimetype='text/html')
    purge_in_varnish(filename)
