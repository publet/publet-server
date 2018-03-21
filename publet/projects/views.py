import json
from annoying.decorators import render_to
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden, Http404
)
from tastypie.authentication import ApiKeyAuthentication
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from publet.groups.models import Group
from publet.projects.models import (
    Publication, Article, change_publication_group, Readability, Theme, Event,
    PublicationSocialGateEntry, find_block, get_block_type
)
from publet.projects.api import PublicationResource, ThemeResource
from publet.projects.forms import ChangeGroupForm
from publet.projects import tasks
from publet.utils.metrics import Meter
from publet.analytics.models import Event as AnalyticsEvent
from publet.analytics.core import (
    get_mean_engaged_data, get_social_data, get_social_data_per_block
)
from publet.third.models import Integration

HOST = getattr(settings, 'HOST', None)
THEME_EDITOR_BASE_URL = getattr(settings, 'THEME_EDITOR_BASE_URL', None)


@login_required
@render_to('publications/publication-detail.html')
def publication_detail(request, group_slug, publication_slug):
    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)

    if not request.user.is_superuser:
        if publication not in request.user.get_publications():
            raise Http404

    events = Event.objects.for_publication(publication)

    pdf_imports_in_progress = publication.get_pdf_imports_in_progress()

    return {
        'page': 'detail',
        'group': group,
        'publication': publication,
        'events': events,
        'can_user_edit': group.can_user_edit(request.user),
        'can_user_edit_themes': group.can_user_edit_themes(request.user),
        'pdf_imports_in_progress': pdf_imports_in_progress
    }


@login_required
@render_to('publications/publication-analytics.html')
def publication_detail_data(request, group_slug, publication_slug):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member or not member.can_user_view_publication_data():
        raise Http404

    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)
    percent_read = {
        'articles': AnalyticsEvent.objects.get_percent_read(publication)
    }
    engaged_data = get_mean_engaged_data(publication)
    engaged_data = json.dumps(engaged_data)

    social = json.dumps(get_social_data(publication.pk))
    per_block_social = get_social_data_per_block(publication.pk)
    per_block_referrals = PublicationSocialGateEntry.objects.per_block(
        publication)
    unique_visitors = AnalyticsEvent.objects.get_unique_visitors(publication)
    server_unique_visitors = AnalyticsEvent.objects.get_server_unique_visitors(
        publication)
    pageviews = AnalyticsEvent.objects.get_pageviews(publication)
    server_pageviews = AnalyticsEvent.objects.get_server_pageviews(publication)

    sessions = AnalyticsEvent.objects.get_sessions(publication.pk)
    num_sessions = len(sessions)
    dropoff = AnalyticsEvent.objects.get_drop_off_report(publication,
                                                         sessions=sessions)
    dropoff = list(dropoff)

    readers = AnalyticsEvent.objects.get_publication_readers(publication.pk)

    gate_class = publication.get_gate_class()

    conversion_count = gate_class.objects.conversion_count(publication)
    conversions = gate_class.objects.for_publication(publication, days=30)
    conversions_table = gate_class.objects.as_table(publication, days=30,
                                                    conversions=conversions)

    return {
        'page': 'data',
        'group': group,
        'publication': publication,
        'can_user_edit': group.can_user_edit(request.user),
        'can_user_edit_themes': group.can_user_edit_themes(request.user),
        'engaged_data': engaged_data,
        'read_data': percent_read,
        'social': social,
        'per_block_social': json.dumps(per_block_social),
        'per_block_referrals': per_block_referrals,
        'per_block_referrals_json': json.dumps(per_block_referrals),
        'pageviews': pageviews,
        'unique_visitors': unique_visitors,
        'conversion_count': conversion_count,
        'server_pageviews': server_pageviews,
        'server_unique_visitors': server_unique_visitors,
        'num_sessions': num_sessions,
        'readers': readers,
        'conversions': conversions,
        'conversions_table': conversions_table,
        'dropoff': dropoff
    }


@login_required
def publication_conversions_csv_download(request, group_slug,
                                         publication_slug):
    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)
    member = group.get_membership(request.user)

    if not member or not member.can_user_view_publication_data():
        raise Http404

    gate_class = publication.get_gate_class()
    conversions_csv = gate_class.objects.as_csv(publication, days=None)

    response = HttpResponse(conversions_csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    return response


@login_required
@render_to('articles/article-detail.html')
def article_detail(request, group_slug, publication_slug, article_slug):
    group = get_object_or_404(Group, slug=group_slug)
    article = get_object_or_404(Article, slug=article_slug,
                                publication__group=group)

    if not request.user.is_superuser:
        if article.publication not in request.user.get_publications():
            raise Http404

    draft_mode = request.GET.get('draft', False) or article.is_draft

    from api import FullFlavorResource
    ffr = FullFlavorResource()
    flavors = article.publication.theme.flavor_set.all()
    flavors = ffr.serialize_items(flavors)

    events = Event.objects.for_article(article)
    articles = article.publication.get_articles()
    integrations = group.get_integrations()
    integrations = dict([(str(i.slug), str(i.name),) for i in integrations])

    return {
        'group': group,
        'article': article,
        'articles': articles,
        'pagination': article.publication.pagination,
        'events': events,
        'can_user_edit': group.can_user_edit(request.user),
        'draft_mode': draft_mode,
        'flavors': flavors,
        'integrations': integrations
    }


@csrf_exempt
@login_required
def user_basic_and_pro(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    # TODO this is just a stopgap that should be replaced with an
    # even more secure method that doesn't dump all of the users
    # into the client #1069
    qs = get_user_model().objects.filter(
        account_type__in=['B', 'P']).only('id', 'username')
    # tastypie endpoints want to see resource_uri rather than id
    objects = [{
        'username': user.username,
        'email': user.email,
        'resource_uri': '/api/user/{}/'.format(user.id)
        } for user in qs.all()]
    res = {'objects': objects}
    return HttpResponse(json.dumps(res), content_type='application/json')


@csrf_exempt
@login_required
def reorder_article(request, article_pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    article = get_object_or_404(Article, pk=article_pk)
    member = article.publication.group.get_membership(request.user)

    if not member.can_user_reorder_articles():
        return HttpResponseForbidden()

    args = json.loads(request.body)
    res = article.reorder(block_type_ids=args['block_type_ids'])
    res['modified'] = article.modified.isoformat()

    return HttpResponse(json.dumps(res), content_type='application/json')


@csrf_exempt
@login_required
def reorder_publication(request, publication_pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    publication = get_object_or_404(Publication, pk=publication_pk)
    member = publication.group.get_membership(request.user)

    if not member.can_user_reorder_articles():
        return HttpResponseForbidden()

    args = json.loads(request.body)
    res = publication.reorder(article_ids=args['article_ids'])

    return HttpResponse(json.dumps(res), content_type='application/json')


@csrf_exempt
@login_required
def duplicate_publication(request, publication_pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    publication = get_object_or_404(Publication, pk=publication_pk)
    publication_resource = PublicationResource()
    new_publication = publication.duplicate()
    uri = publication_resource.get_resource_uri(new_publication)

    return HttpResponse(uri, content_type='text/plain')


@csrf_exempt
@login_required
def republish_publication(request, publication_pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    publication = get_object_or_404(Publication, pk=publication_pk)
    publication.update_custom_publication_data()

    return HttpResponse('', content_type='text/plain')


@login_required
@render_to('change_group.html')
def change_group_admin_view(request, pk):
    if not request.user.has_perm('projects.change_publication'):
        return HttpResponseForbidden()

    publication = get_object_or_404(Publication, pk=pk)

    if request.method == 'POST':
        form = ChangeGroupForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data.get('group')
            change_publication_group(publication, group)
            messages.info(request, 'Successfully changed')
            return redirect('admin:projects_publication_change',
                            publication.pk)

    else:
        form = ChangeGroupForm()

    return {
        'form': form,
        'publication': publication
    }


@render_to('chrome.html')
def chrome_extension(request):
    # Support both API key and session authentication

    if not request.user.is_authenticated():
        auth = ApiKeyAuthentication()
        auth._unauthorized = lambda: False

        if not auth.is_authenticated(request):
            return HttpResponseForbidden()

    groups = request.user.get_groups()

    Meter('chrome.clicked').inc()

    return {
        'groups': groups
    }


@csrf_exempt
def readability(request, pk):
    # Support both API key and session authentication

    if request.method != 'POST':
        return HttpResponseForbidden()

    if not request.user.is_authenticated():

        auth = ApiKeyAuthentication()
        auth._unauthorized = lambda: False

        if not auth.is_authenticated(request):
            return HttpResponseForbidden()

    url = request.POST.get('url')

    if not url:
        return HttpResponseForbidden()

    publication = get_object_or_404(Publication, pk=pk)
    r = Readability.objects.create(url=url, publication=publication)
    tasks.parse_readability.delay(r)

    Meter('chrome.submitted').inc()

    return HttpResponse()


@login_required
@render_to('themes/theme-list.html')
def theme_list(request):
    if not request.user.is_superuser:
        raise Http404

    return {
        'themes': Theme.objects.all().order_by('id')
    }


@login_required
@render_to('themes/theme-list.html')
def group_theme_list(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)

    if not group.can_user_edit_themes(request.user):
        raise Http404

    themes = group.theme_set.all()
    new_themes = group.newtheme_set.all()

    return {
        'themes': themes,
        'new_themes': new_themes,
        'group': group,
        'url': THEME_EDITOR_BASE_URL
    }


@login_required
@render_to('themes/theme-detail.html')
def theme_detail(request, group_slug, theme_slug):
    theme = get_object_or_404(Theme, slug=theme_slug)
    group = get_object_or_404(Group, slug=group_slug)

    if not group.can_user_edit_themes(request.user):
        raise Http404

    theme_resource = ThemeResource()

    bundle = theme_resource.build_bundle(obj=theme, request=request)
    bundle = theme_resource.full_dehydrate(bundle)

    data = theme_resource.serialize(request, bundle, 'application/json')
    return {
        'theme': data,
        'group': group
    }


@login_required
def article_draft(request, group_slug, publication_slug, article_slug):
    if request.method != 'POST':
        raise Http404

    action = request.POST.get('action', None)

    if action not in ['start', 'publish', 'trash']:
        raise Http404

    article = get_object_or_404(Article, slug=article_slug)

    if action == 'start':
        draft = article.create_draft()
        url = reverse('article-detail',
                      kwargs=dict(group_slug=group_slug,
                                  publication_slug=article.publication.slug,
                                  article_slug=draft.slug))
        return redirect(url + '?draft=true')

    if action == 'trash':
        parent = article.parent
        article.delete()
        return redirect('article-detail', group_slug=group_slug,
                        publication_slug=article.publication.slug,
                        article_slug=parent.slug)

    if action == 'publish':
        parent = article.parent
        article.parent = None
        article.is_draft = False
        article.save()

        parent.delete()

        return redirect('article-detail', group_slug=group_slug,
                        publication_slug=article.publication.slug,
                        article_slug=article.slug)


def internal_block_id(request, block_id):
    block = find_block(block_id)

    if not block:
        raise Http404

    args = (block.article.publication.group.slug,
            block.article.publication.slug,)

    url = HOST + reverse('preview-publication-html', args=args)
    url += ('#block-' + str(block.pk))
    return redirect(url)


def user_identity(request):
    seen_gate = request.session.get('seen_gate', {})
    seen_pages = request.session.get('seen_pages', [])
    user_id = 0 if request.user.is_anonymous() else request.user.pk

    data = {
        'seen': seen_gate,
        'seen_pages': seen_pages,
        'user_id': user_id
    }

    response = HttpResponse(json.dumps(data), content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@login_required
def integration_submission_handler(request, block_type, block_id):
    if request.method != 'POST':
        raise Http404

    req_body = json.loads(request.body)
    integration_slug = req_body.get('integration', None)
    integration = get_object_or_404(Integration, slug=integration_slug)

    Class = get_block_type(block_type)

    if not Class:
        raise Http404

    block = Class.objects.get(pk=block_id)
    block.submit_to_integration(integration)

    return HttpResponse(status=201)
