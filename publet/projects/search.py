"""
Elasticsearch related functions
"""
from django.conf import settings
from elasticsearch import Elasticsearch


ELASTICSEARCH_CONFIG = getattr(settings, 'ELASTICSEARCH_CONFIG', None)


def get_es():
    return Elasticsearch(ELASTICSEARCH_CONFIG)


def _search_blocks(term, **kwargs):
    es = get_es()

    content_query = {
        'match': {
            'content': term
        }
    }

    if not kwargs:
        # Search everything

        body = {
            'query': content_query
        }

        return es.search(index='blocks', doc_type='block', body=body)

    filter_obj = None

    if 'group' in kwargs:
        filter_obj = {
            'term': {
                'group_id': kwargs['group'].pk
            }
        }

    if 'publication' in kwargs:
        filter_obj = {
            'term': {
                'publication_id': kwargs['publication'].pk
            }
        }

    if 'hub' in kwargs:
        ids = [p.pk for p in kwargs['hub'].publications.all()]
        filter_obj = {
            'terms': {
                'publication_id': ids
            }
        }

    body = {
        'query': {
            'filtered': {
                'query': content_query,
                'filter': filter_obj
            }
        },
        'highlight': {
            'encoder': 'html',
            'fields': {
                'content': {}
            }
        }
    }

    return es.search(index='blocks', doc_type='block', body=body)


def _search_publications(term, **kwargs):
    es = get_es()

    content_query = {
        'match': {
            '_all': term
        }
    }

    if not kwargs:
        # Search everything

        body = {
            'query': content_query
        }

        return es.search(index='publications', doc_type='publication',
                         body=body)

    filter_obj = None

    if 'group' in kwargs:
        filter_obj = {
            'term': {
                'group_id': kwargs['group'].pk
            }
        }

    if 'publication' in kwargs:
        filter_obj = {
            'term': {
                'publication_id': kwargs['publication'].pk
            }
        }

    if 'hub' in kwargs:
        ids = [p.pk for p in kwargs['hub'].publications.all()]
        filter_obj = {
            'terms': {
                'publication_id': ids
            }
        }

    body = {
        'query': {
            'filtered': {
                'query': content_query,
                'filter': filter_obj
            }
        },
        'highlight': {
            'encoder': 'html',
            'fields': {
                'name': {},
                'topics': {},
                'keywords': {},
            }
        }
    }

    return es.search(index='publications', doc_type='publication', body=body)


def _search(term, **kwargs):
    blocks = _search_blocks(term, **kwargs)['hits']['hits']
    publications = _search_publications(term, **kwargs)['hits']['hits']

    return publications + blocks


def search_group(group, term):
    return _search(term, group=group)


def search_hub(hub, term):
    return _search(term, hub=hub)


def search_publication(publication, term):
    return _search(term, publication=publication)


def search_publet(term):
    """
    Search all blocks.  Caller is responsible for permission checking.
    """
    return _search(term)
