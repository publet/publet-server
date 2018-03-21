import os
from subprocess import call

import requests
from django.core.management import call_command
from django.conf import settings
from django_rq import job
from annoying.functions import get_object_or_None

from publet.utils.utils import get_image_dimensions
from publet.utils.metrics import Timer, Occurrence


MANAGEPY_DIR = getattr(settings, 'MANAGEPY_DIR', None)
TESTING = getattr(settings, 'TESTING', False)
GENERATED_PUBLICATIONS_PATH = getattr(settings, 'GENERATED_PUBLICATIONS_PATH',
                                      None)


@job
def generate_pdf(instance):
    instance._render_css()
    instance._render_js()
    instance._render_html()
    instance._render_pdf()


@job
def generate_mobi(instance):
    instance._render_mobile_html_and_css()
    instance._render_mobi()


@job
def generate_epub(instance):
    instance._render_mobile_html_and_css()
    instance._render_epub()


@job
def generate_html_zip(instance):
    instance._render_css()
    instance._render_js()
    instance._render_html()
    instance._render_html_zip()


@job
def generate_jpg(instance):
    instance._render_css()
    instance._render_js()
    instance._render_html()
    instance._render_jpg()


@job
def republish_publication(instance):
    return instance._update_custom_publication_data()


@job
def collectstatic():
    if TESTING:
        return

    call_command('collectstatic', interactive=False)

    if os.path.exists(GENERATED_PUBLICATIONS_PATH):
        call('chmod -R 775 {}'.format(GENERATED_PUBLICATIONS_PATH), shell=True)

    Occurrence('collectstatic').mark()


@job
def update_theme_on_disk(theme):
    theme.update_theme_on_disk()


@job
def get_dimensions_for_photo(photo_pk):
    """
    ______________
    < this is dumb >
    --------------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||
    """
    from publet.projects.models import Photo
    photo = get_object_or_None(Photo, pk=photo_pk)

    if not photo:
        return

    fp = 'https://www.filepicker.io'
    cdn = 'https://cdn.publet.com'

    url = photo.image_url.replace(cdn, fp)

    width, height = get_image_dimensions(url)
    photo.width = width
    photo.height = height
    photo.save()


@job
def get_vimeo_metadata(video_block_pk):
    from publet.projects.models import VideoBlock
    video = VideoBlock.objects.get(pk=video_block_pk)
    video.populate_vimeo_metadata()


@job
def parse_readability(instance):
    r = requests.get(instance.url)

    if r.status_code != 200:
        raise Exception('Article not found')

    instance.parse(r.content)


@job
def rebuild_theme(theme):
    try:
        theme.save(update_on_disk=False)
        theme.update_theme_on_disk(collect_static=False)
        return True
    except:
        raise Exception('failed theme {}\n'.format(theme.slug))


@job
def rebuild_pdf(publication):
    return generate_pdf(publication)


@job
def rebuild_screenshot(publication):
    return generate_jpg(publication)


@job
def rebuild_themes(themes):
    with Timer('utils.rebuild-themes'):
        for t in themes:
            rebuild_theme(t)


@job
def rebuild_all_pdfs(publications):
    with Timer('utils.rebuild-pdfs'):
        for p in publications:
            rebuild_pdf(p)


@job
def rebuild_all_screenshots(publications):
    with Timer('utils.rebuild-pdfs'):
        for p in publications:
            rebuild_screenshot(p)


@job
def import_pdf_upload(upload_pk):
    from publet.projects.models import PDFUpload
    pdf = PDFUpload.objects.get(pk=upload_pk)
    pdf.import_to_publication()


@job
def index_text_block(block_id):
    from publet.projects.models import TextBlock, index_text_block
    tb = get_object_or_None(TextBlock, pk=block_id)
    index_text_block(tb)


@job
def index_publication(publication_id):
    from publet.projects.models import Publication, index_publication
    publication = get_object_or_None(Publication, pk=publication_id)
    index_publication(publication)


@job
def upload_new_publication(publication_id):
    from publet.projects.models import Publication
    publication = get_object_or_None(Publication, pk=publication_id)

    if not publication:
        return

    if not publication.new_style:
        return

    publication.upload()


@job
def upload_new_article(article_id):
    from publet.projects.models import NewArticle
    article = get_object_or_None(NewArticle, pk=article_id)

    if not article:
        return

    article.upload()
