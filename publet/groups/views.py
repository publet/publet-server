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
import json

from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from publet.groups.models import Group, GroupHub, GroupMember
from publet.groups.forms import GroupHubForm
from publet.payments.models import Purchase
from publet.feedback.forms import IntegrationFeedbackForm
from publet.projects.search import search_hub
from publet.projects.models import format_es_results


@login_required
@render_to('groups/group-detail.html')
def group_detail(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member or not member.can_user_read_group():
        raise Http404

    return {
        'group': group,
        'can_user_edit': member.can_user_edit_group(),
        'can_user_edit_themes': member.can_user_edit_themes(),
        'can_edit_members': member.can_user_edit_members()
    }


@login_required
@render_to('groups/groups-list.html')
def groups_list(request):

    groups = request.user.get_groups().order_by('name')

    return {
        'groups': groups
    }


def profile_detail(request, profile_slug):
    group = get_object_or_404(Group, slug=profile_slug)
    user = request.user

    if user.is_authenticated():
        already_purchased = get_object_or_None(Purchase, group=group,
                                               user=user)
        in_user_groups = group in user.get_groups()
        subscribed = group.is_user_subscribed(user)
    else:
        already_purchased = None
        in_user_groups = []
        subscribed = False

    if in_user_groups or subscribed:
        return render_to_response('groups/profile-detail.html', {
            'group': group,
            'already_purchased': already_purchased
        }, context_instance=RequestContext(request))

    splash = group.get_splash_publication()
    data = {
        'group': group
    }

    if splash:
        data['publication'] = splash
        return render_to_response(splash.get_html_template(), data,
                                  context_instance=RequestContext(request))

    return render_to_response(group.get_splash_template(), data,
                              context_instance=RequestContext(request))


@login_required
@render_to('groups/group-integrations.html')
def integrations(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)

    if request.method == 'POST':
        form = IntegrationFeedbackForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.info(request, 'Feedback submitted!')
            return redirect('integrations', group.slug)
    else:
        form = IntegrationFeedbackForm()
    return {
        'group': group,
        'form': form,
        'integrations': group.integration_set.all()
    }


@csrf_exempt
def search_group_api(request, group_pk, hub_pk):
    # Only live publications are ever indexed so we don't need to bother
    # checking it here.

    get_object_or_404(Group, pk=group_pk)
    hub = get_object_or_404(GroupHub, pk=hub_pk)

    query = request.GET.get('query', None)

    if not query:
        res = []
    else:
        res = search_hub(hub, query)['hits']['hits']
        res = format_es_results(res)

    return HttpResponse(json.dumps(res), content_type='application/json')


@login_required
@render_to('groups/group-hubs.html')
def hubs(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member.can_user_edit_group():
        return HttpResponseForbidden()

    hubs = group.grouphub_set.all()

    return {
        'group': group,
        'hubs': hubs
    }


@login_required
@render_to('groups/group-hub-add.html')
def hubs_add(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)

    member = group.get_membership(request.user)

    if not member.can_user_edit_group():
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = GroupHubForm(request.POST, group=group)

        if form.is_valid():
            hub = form.save(commit=False)
            hub.group = group
            hub.created_by = request.user
            hub.save()
            form.save_m2m()
            messages.info(request, 'Hub created!')
            return redirect('group-hubs', group.slug)
    else:
        form = GroupHubForm(group=group)

    return {
        'group': group,
        'hubs': hubs,
        'form': form
    }


@login_required
@render_to('groups/group-hub-detail.html')
def hub_detail(request, group_slug, hub_slug):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member.can_user_edit_group():
        return HttpResponseForbidden()

    hub = get_object_or_404(GroupHub, slug=hub_slug, group=group)
    publications = hub.publications.all()

    return {
        'group': group,
        'hub': hub,
        'publications': publications
    }


@login_required
@render_to('groups/group-hub-delete.html')
def hub_delete(request, group_slug, hub_slug):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member.can_user_edit_group():
        return HttpResponseForbidden()

    hub = get_object_or_404(GroupHub, slug=hub_slug, group=group)

    if request.method == 'POST':
        hub.delete()
        messages.info(request, 'Hub deleted!')
        return redirect('group-hubs', group.slug)

    return {
        'group': group,
        'hub': hub
    }


def hub_live(request, group_slug, hub_slug):
    group = get_object_or_404(Group, slug=group_slug)
    hub = get_object_or_404(GroupHub, slug=hub_slug, group=group)
    publications = hub.publications.filter(status='live')

    sort = request.GET.get('sort', None)

    if sort and sort in ['published', 'name']:
        publications = publications.order_by(sort)

    data = {
        'group': group,
        'hub': hub,
        'publications': publications,
        'sort': sort
    }

    return render_to_response(group.get_landing_template(), data,
                              context_instance=RequestContext(request))


@login_required
@render_to('groups/group-members.html')
def members(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    current_members = group.groupmember_set.all()
    current_user_membership = group.get_membership(request.user)
    can_edit_members = current_user_membership.can_user_edit_members()
    can_invite_users = current_user_membership.can_user_invite_users_to_group()

    return {
        'current_members': current_members,
        'group': group,
        'current_user_membership': current_user_membership,
        'can_edit_members': can_edit_members,
        'can_invite_users': can_invite_users
    }


@login_required
@render_to('groups/group-members-add.html')
def members_add(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)

    current_user_membership = group.get_membership(request.user)
    can_edit_members = current_user_membership.can_user_edit_members()

    if not can_edit_members:
        raise HttpResponseForbidden()

    user = None
    not_found = False

    if request.method == 'POST':
        action = request.POST.get('action', None)

        if action == 'find':
            identifier = request.POST.get('identifier', None)
            qs = get_user_model().objects.filter(Q(username=identifier) |
                                                 Q(email=identifier))
            qs = qs.exclude(pk=request.user.pk)

            if qs.exists():
                user = qs[0]
            else:
                user = None
                not_found = True

        elif action == 'add':
            user_pk = request.POST.get('user', None)
            role = request.POST.get('role', None)
            user = get_object_or_404(get_user_model(), pk=int(user_pk))

            if not user or not role:
                raise Exception('hi')

            GroupMember.objects.create(group=group, role=role, user=user)
            messages.info(request, 'User added!')
            return redirect('group-members', group.slug)

    return {
        'member': user,
        'not_found': not_found,
        'group': group
    }


@login_required
@render_to('groups/group-members-change.html')
def change_member(request, group_slug, member_pk):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member.can_user_edit_members():
        return redirect('group-detail', group.slug)

    user = get_object_or_404(get_user_model(), pk=member_pk)
    member = group.get_membership(user, ignore_superuser=True)

    if request.method == 'POST':
        role = request.POST.get('role', None)

        member.role = role
        member.save()

        messages.info(request, 'Permissions changed!')
        return redirect('group-members', group.slug)

    return {
        'group': group,
        'member': member
    }


@login_required
@render_to('groups/group-members-delete.html')
def delete_member(request, group_slug, member_pk):
    group = get_object_or_404(Group, slug=group_slug)
    member = group.get_membership(request.user)

    if not member.can_user_edit_members():
        return redirect('group-detail', group.slug)

    user = get_object_or_404(get_user_model(), pk=member_pk)
    member = group.get_membership(user, ignore_superuser=True)

    if request.method == 'POST':
        member.delete()
        messages.info(request, 'User deleted!')
        return redirect('group-members', group.slug)

    return {
        'group': group,
        'member': member
    }


def hub_live_search(request, group_slug, hub_slug):
    group = get_object_or_404(Group, slug=group_slug)
    hub = get_object_or_404(GroupHub, slug=hub_slug, group=group)
    publications = hub.publications.filter(status='live')

    query = request.GET.get('query', None)

    if not query:
        return redirect('group-hub-live', group.slug, hub.slug)

    res = search_hub(hub, query)
    res = format_es_results(res)

    data = {
        'group': group,
        'hub': hub,
        'publications': publications,
        'results': res,
        'query': query
    }

    return render_to_response(group.get_search_result_template(), data,
                              context_instance=RequestContext(request))
