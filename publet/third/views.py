from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from annoying.decorators import render_to
from buffer import BufferAuthService, submit_to_buffer

from publet.groups.models import Group
from models import BufferConfig, Integration, BufferProfile
from tasks import import_buffer_profiles, import_buffer_user_data

BUFFER_OAUTH_CALLBACK = getattr(settings, 'BUFFER_OAUTH_CALLBACK')
BUFFER_OAUTH_CLIENT_ID = getattr(settings, 'BUFFER_OAUTH_CLIENT_ID')
BUFFER_OAUTH_CLIENT_SECRET = getattr(settings, 'BUFFER_OAUTH_CLIENT_SECRET')

PUBLET_LOGO_URL = ('https://www.filepicker.io/api/file/bRBbaYSXRf6Kl4lcqchy'
                   '?signature=9a800a1507049e983e3c39198072b927979cdacaf89b7c2'
                   '37f8f283de1e5667c&policy=eyJjYWxsIjogWyJyZWFkIiwgImNvbnZlc'
                   'nQiXSwgImV4cGlyeSI6ICIyNTI0NjQwNDAwIn0=')


@login_required
@render_to('groups/integration-error.html')
def buffer_callback(request):
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    error = request.GET.get('error', None)

    if not code:
        return {
            'error': error,
            'provider': 'Buffer'
        }

    group = get_object_or_404(Group, slug=state)
    service = BufferAuthService(BUFFER_OAUTH_CLIENT_ID,
                                BUFFER_OAUTH_CLIENT_SECRET,
                                BUFFER_OAUTH_CALLBACK)
    access_token = service.get_access_token(code)
    integration = Integration.objects.create(name='Buffer', group=group,
                                             created_by=request.user)
    BufferConfig.objects.create(access_token=access_token,
                                integration=integration,
                                created_by=request.user)
    import_buffer_profiles.delay(integration.pk)
    import_buffer_user_data.delay(integration.pk)
    messages.info(request, 'Integration added!')
    return redirect('integrations', group.slug)


@login_required
def buffer_start(request):
    group = request.GET.get('group', None)
    service = BufferAuthService(BUFFER_OAUTH_CLIENT_ID,
                                BUFFER_OAUTH_CLIENT_SECRET,
                                BUFFER_OAUTH_CALLBACK)
    return redirect(service.get_authorize_url_with_state(group))


def buffer_integration_detail(request, integration):
    profiles = BufferProfile.objects.filter(token__integration=integration)
    conf = integration.bufferconfig

    if request.method == 'POST':
        task = request.POST.get('task', None)

        if task == 'import':
            import_buffer_profiles.delay(integration.pk)
            return redirect('integration-detail', integration.slug)

        if task == 'test':
            success = submit_to_buffer(integration, 'test post',
                                       PUBLET_LOGO_URL)

            if success:
                message = 'Message sent successfully!'
            else:
                message = 'Failed to send message.  Try again later please.'

            messages.info(request, message)
            return redirect('integration-detail', integration.slug)

    return {
        'integration': integration,
        'profiles': profiles,
        'conf': conf,
        'type': 'buffer'
    }


@login_required
@render_to('integration-detail.html')
def integration_detail(request, integration_slug):
    integration = get_object_or_404(Integration, slug=integration_slug)

    if integration.name == 'Buffer':
        return buffer_integration_detail(request, integration)


@login_required
@render_to('integration-delete.html')
def integration_delete(request, integration_slug):
    integration = get_object_or_404(Integration, slug=integration_slug)

    if request.method == 'POST':
        integration.delete()
        messages.info(request, 'Integration deleted')
        return redirect('integrations', integration.group.slug)

    return {
        'integration': integration
    }
