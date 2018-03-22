"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import json
import logging
from datetime import datetime
import HTMLParser
from annoying.decorators import ajax_request, render_to
from annoying.functions import get_object_or_None
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from publet.groups.models import Group
from publet.projects.models import (
    Publication, Article, TextBlock, get_block_type
)
from publet.utils.encode import encode
from publet.utils.metrics import Meter
from publet.analytics.models import Event
from publet.outputs.forms import PasswordForm


logger = logging.getLogger(__name__)
APP_CACHE_TIMESTAMP = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
APP_CACHE_ENABLED = getattr(settings, 'APP_CACHE_ENABLED', False)
HOST = getattr(settings, 'HOST', None)


def get_tracking_data_from_meta(meta):
    return {
        'ip': meta.get('HTTP_X_REAL_IP'),
        'referrer': meta.get('HTTP_REFERER'),
        'user_agent': meta.get('HTTP_USER_AGENT')
    }


def _custom(publication):
    path = '/custom-publications/{}/index.html'.format(
        publication.slug)
    response = HttpResponse()

    response['Content-Type'] = ""
    response['X-Accel-Redirect'] = path

    return response


@login_required
def download_publication_html(request, publication_slug):

    publication = get_object_or_404(Publication, slug=publication_slug)

    if publication not in request.user.get_publications():
        raise PermissionDenied

    publication.render_html_zip()

    with open('{}/html.zip'.format(publication.get_render_dir()),
              'r') as zip_file:
        zip_output = zip_file.read()

    return HttpResponse(zip_output, content_type='application/x-download')


@login_required
def download_publication_epub(request, publication_slug):

    publication = get_object_or_404(Publication, slug=publication_slug)

    if publication not in request.user.get_publications():
        raise PermissionDenied

    publication.render_epub()

    with open('{}/{}.epub'.format(publication.get_render_dir(),
                                  publication.slug),
              'r') as epub_file:
        epub_output = epub_file.read()

    return HttpResponse(epub_output, content_type='application/x-download')


@login_required
def download_publication_mobi(request, publication_slug):

    publication = get_object_or_404(Publication, slug=publication_slug)

    if publication not in request.user.get_publications():
        raise PermissionDenied

    publication.render_mobi()

    with open('{}/{}.mobi'.format(publication.get_render_dir(),
                                  publication.slug),
              'r') as mobi_file:
        mobi_output = mobi_file.read()

    return HttpResponse(mobi_output, content_type='application/x-download')


@login_required
def download_publication_pdf(request, publication_slug):

    publication = get_object_or_404(Publication, slug=publication_slug)

    if publication not in request.user.get_publications():
        raise PermissionDenied

    publication.render_pdf()

    with open('{}/{}.pdf'.format(publication.get_render_dir(),
                                 publication.slug),
              'r') as pdf_file:
        pdf_output = pdf_file.read()

    return HttpResponse(pdf_output, content_type='application/x-download')


def _publication(request, publication, data):
    is_mobile = request.is_mobile
    is_custom_domain = request.is_custom_domain

    key = publication.get_cache_key_html(page=data.get('page', 1),
                                         is_mobile=is_mobile,
                                         is_custom_domain=is_custom_domain)

    if not data['should_show_draft']:
        html = cache.get(key)

        if html:
            return html

    html = render_to_response(publication.get_html_template(), data,
                              context_instance=RequestContext(request))

    if not data['should_show_draft']:
        # Timeout None means cache it forever
        cache.set(key, html, timeout=None)

    return html


def preview_publication_html(request, group_slug, publication_slug, page=1):
    """
    If the current user is a member of the group that this publication
    belongs to, show them the html preview.

    If the publication is hidden and the user doesn't belong to the
    publication's group, don't show the preview.
    """
    group = get_object_or_404(Group, slug=group_slug)
    publication = Publication.objects.by_slug(publication_slug,
                                              group_slug=group.slug)

    if not publication:
        raise Http404

    if publication.hosted_password:
        member = group.get_membership(request.user)
        key = 'password-submitted:{}'.format(publication.pk)
        data = {
            'hide_login_signup': True
        }

        if not member and not request.session.get(key):
            if request.method == 'POST':
                form = PasswordForm(request.POST)

                if form.is_valid():

                    p = form.cleaned_data.get('password')

                    if p == publication.hosted_password:
                        request.session[key] = True
                        return redirect(request.path)

                    data['error'] = "Password incorrect.  Please try again."

            else:
                form = PasswordForm()

            data['form'] = form
            return render_to_response('outputs/password.html', data,
                                      context_instance=RequestContext(request))

    seen_pages = request.session.get('seen_pages', {})
    seen_pages_pub = set(seen_pages.get(publication.pk, []))
    seen_pages_pub.add(page)
    seen_pages[publication.pk] = list(seen_pages_pub)
    request.session['seen_pages'] = seen_pages

    if 'nogate' in request.GET:
        seen_gate = request.session.get('seen_gate', {})
        seen_gate[publication.pk] = True
        request.session['seen_gate'] = seen_gate

    if request.user.is_authenticated():
        groups = request.user.get_groups()
        user = request.user
    else:
        groups = []
        user = None

    data = {
        'app_cache_enabled': APP_CACHE_ENABLED,
        'group': group,
        'publication': publication,
        'pagination': publication.pagination,
        'output_type': 'html',
        'page': int(page),
        'should_show_draft': 'draft' in request.GET
    }

    if publication.pagination == 'h':
        articles = publication.get_articles().order_by('order')
        p = Paginator(articles, 1)

        try:
            p = p.page(page)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results
            p = p.page(p.num_pages)

        data['p'] = p
        data['range'] = range(1, p.paginator.num_pages + 1)

    in_user_groups = request.user.is_superuser or publication.group in groups

    if publication.status == 'custom' and not publication.price:
        return _custom(publication)

    if in_user_groups or publication.has_user_already_purchased(user):
        if publication.status == 'custom':
            return _custom(publication)

        return _publication(request, publication, data)

    if publication.status == 'hidden':
        raise Http404

    if publication.status == 'live' and not publication.price:
        return _publication(request, publication, data)

    splash = publication.get_splash_article()

    if splash:
        return render_to_response(splash.publication.get_html_template(), {
            'articles': [splash]
        }, context_instance=RequestContext(request))

    return render_to_response(publication.get_splash_template(), data,
                              context_instance=RequestContext(request))


def custom_publication_resource(request, path):
    if 'favicon' in path:
        raise Http404

    parts = path.split('/')
    publication_slug = parts[1]

    path = '/'.join(parts[2:len(parts)])
    path = '/custom-publications/{}/{}'.format(publication_slug, path)
    response = HttpResponse()

    response['Content-Type'] = ""
    response['X-Accel-Redirect'] = path

    return response


def protected_file(request, article_slug=None, publication_slug=None):
    assert article_slug or publication_slug

    original_slug = article_slug or publication_slug

    slug, ext = os.path.splitext(original_slug)

    if ext not in ['.pdf', '.zip', '.epub', '.mobi', '.ipa']:
        raise Http404

    if publication_slug:
        path_template = '/protected/publications/{}/{}'
        instance = get_object_or_404(Publication, slug=slug)

        if instance.status != 'live':

            if not request.user.is_authenticated():
                raise PermissionDenied

            if instance not in request.user.get_publications():
                raise PermissionDenied

    elif article_slug:
        path_template = '/protected/{}/{}'
        instance = get_object_or_404(Article, slug=slug)

        if instance.publication.status != 'live':
            if not request.user.is_authenticated():
                raise PermissionDenied

            if instance not in request.user.get_articles():
                raise PermissionDenied

    else:
        raise Http404

    path_on_disk = instance.filename_for_format(ext[1:])

    if os.path.exists(path_on_disk):
        path_slug = instance.base_filename_for_format(ext[1:])
    else:
        pub_render_dir = instance.get_render_dir()
        files_of_type = filter(lambda x: x.endswith(ext),
                               os.listdir(pub_render_dir))
        files_of_type.sort()
        files_of_type.reverse()

        try:
            path_slug = files_of_type[0]
        except IndexError:
            path_slug = None

    path = path_template.format(instance.slug, path_slug)
    response = HttpResponse()

    response['Content-Type'] = ""
    response['X-Accel-Redirect'] = path

    return response


@ajax_request
@csrf_exempt
def render_request(request):
    raise Http404

    if request.method != 'POST':
        raise Http404

    try:
        POST = json.loads(request.body)
    except ValueError:
        raise Http404

    if 'publication_pk' not in POST:
        raise Http404

    pk = POST.get('publication_pk', None)
    ext = POST.get('extension', None)

    if not pk:
        raise Http404

    if ext not in ['pdf', 'zip', 'epub', 'mobi', 'ios']:
        raise Http404

    instance = get_object_or_404(Publication, pk=pk)

    cache_key = '{}.{}'.format(instance.slug, ext)
    job_id = cache.get(cache_key)

    file_url = instance.get_protected_file_url(ext)

    if job_id:
        logger.info('render request - found job id: {}'.format(job_id))

        res = AsyncResult(job_id)
        res = None
        if res.successful():
            logger.info('render request - job success: {}'.format(job_id))
            cache.delete(cache_key)
            return {'status': 'ready',
                    'path': file_url}
        else:
            return {'status': 'wait'}

    if instance.should_rerender(ext):
        logger.info('render request - rerender: {}'.format(instance.pk))
        task = instance.render_ext(ext)
        cache.set(cache_key, task.id)
        return {'status': 'wait'}

    logger.info('render request - file ready: {}'.format(instance.pk))

    return {'status': 'ready',
            'path': file_url}


def appcache(request):
    """
    Inserting the timestamp busts the app cache on each deploy
    """
    content = """CACHE MANIFEST
# {}
static/css/skeleton/base.css
static/css/skeleton/skeleton.css
static/css/skeleton/layout.css
static/css/outputs/publication.css
static/components/highlightjs/styles/tomorrow.css
static/components/highlightjs/highlight.pack.js
    """.format(APP_CACHE_TIMESTAMP)
    return HttpResponse(content, 'text/cache-manifest')


@render_to('outputs/partials/article.html')
def article_partial(request, article_pk):
    return {
        'article': get_object_or_404(Article, pk=article_pk)
    }


@render_to('outputs/publication.html')
def render_publication_iframe(request, publication_slug):
    """
    iframe output type
    """
    publication = get_object_or_404(Publication, slug=publication_slug)
    return {
        'group': publication.group,
        'publication': publication,
        'output_type': 'html',
        'is_iframe': True,
        'seen_gate': False
    }


@render_to('outputs/publication.html')
def render_publication_frameless(request, publication_slug):
    """
    static output type without doctype, html or body
    """
    publication = get_object_or_404(Publication, slug=publication_slug)
    return {
        'group': publication.group,
        'publication': publication,
        'output_type': 'html',
        'is_iframe': True,
        'remove_body': True,
        'seen_gate': False
    }


def iframe_embed(request, pk):
    obj = get_object_or_404(TextBlock, pk=pk)

    h = HTMLParser.HTMLParser()
    content = h.unescape(obj.content)

    return render_to_response('outputs/iframe.html', {
        'content': content,
        'id': pk
    })


def short_link_redirect(request, block_type, code):
    block_class = get_block_type(block_type)
    pk = encode(code)
    obj = get_object_or_None(block_class, pk=pk)

    if not obj:
        Meter('short-link.not-found').inc()
        raise Http404

    url = obj.link_to_block

    Meter('short-link.hit').inc()
    return redirect(url)


def publication_thumbnail(request, group_slug, publication_slug):
    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)
    path = publication.get_latest_screenshot()

    if not path:
        raise Http404

    _, x = path.split('renders')
    response = HttpResponse()
    response['Content-Type'] = ""
    response['X-Accel-Redirect'] = '/protected' + x
    return response


@login_required
def publication_heatmap(request, group_slug, publication_slug, page=1):
    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)

    heatmap_data = Event.objects.get_per_block_engaged_data_with_colors(
        publication.id)
    heatmap_data = map(lambda x: (x[0], x[1].serialize()), heatmap_data)
    heatmap_data = dict(heatmap_data)

    data = {
        'heatmap': True,
        'heatmap_data': heatmap_data,
        'group': group,
        'publication': publication,
        'pagination': publication.pagination,
        'output_type': 'html',
        'page': int(page)
    }

    if publication.pagination == 'h':
        articles = publication.get_articles().order_by('order')
        p = Paginator(articles, 1)

        try:
            p = p.page(page)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results
            p = p.page(p.num_pages)

        data['p'] = p
        data['range'] = range(1, p.paginator.num_pages + 1)

    return render_to_response(publication.get_heatmap_template(), data,
                              context_instance=RequestContext(request))
