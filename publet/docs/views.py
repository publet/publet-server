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

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404

import misaka


PROJECT_PATH = getattr(settings, 'PROJECT_PATH', None)
DOC_DIR = os.path.join(PROJECT_PATH, '../docs')
USER_TYPE_DIRS = {
    'admin':  ['admin', 'staff', 'pro', 'basic', 'reader'],
    'staff':  ['staff', 'pro', 'basic', 'reader'],
    'pro':    ['pro', 'basic', 'reader'],
    'basic':  ['basic', 'reader'],
    'reader': ['reader'],
    'trial':  ['trial']
}


def file_to_page(filename):
    if not os.path.exists(filename):
        return

    basename = os.path.basename(filename)
    name, _ = basename.split('.')

    title = ' '.join(name.split('-')).capitalize()

    content = open(filename).read()
    html = misaka.html(content, extensions=misaka.EXT_FENCED_CODE)

    section = os.path.basename(os.path.dirname(filename))

    return dict(title=title, html=html, slug=name, path=filename,
                section=section)


def get_user_type(user):
    if user.is_superuser:
        user_type = 'admin'
    elif user.is_staff:
        user_type = 'staff'
    else:
        user_type = user.get_account_type_display().lower()

    return user_type


def get_dirs_for_user(user):
    user_type = get_user_type(user)
    dirs = map(lambda x: 'user-{}'.format(x), USER_TYPE_DIRS[user_type])
    return map(lambda x: os.path.join(DOC_DIR, x), dirs)


def get_section_from_dir(directory):
    docs = map(lambda x: os.path.join(directory, x), os.listdir(directory))
    base = os.path.basename(directory).split('-')[1].capitalize()
    heading = ' '.join([base, 'documentation'])
    return {
        'docs': map(file_to_page, docs),
        'heading': heading
    }


def get_sections_for_user(user):
    user_dirs = get_dirs_for_user(user)
    return map(get_section_from_dir, user_dirs)


def can_user_see_section(user, section):
    name = section.split('-')[1]
    return name in USER_TYPE_DIRS[get_user_type(user)]


# Views -----------------------------------------------------------------------

@login_required
def index(request):
    sections = get_sections_for_user(request.user)
    return render(request, 'docs/index.html', {
        'sections': sections
    })


@login_required
def single(request, section, slug):
    if not can_user_see_section(request.user, section):
        raise Http404

    filename = os.path.join(DOC_DIR, section, slug + '.md')
    page = file_to_page(filename)
    return render(request, 'docs/single.html', {
        'page': page
    })
