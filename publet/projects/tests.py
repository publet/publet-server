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
from urlparse import urlparse, parse_qs

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings

from publet.groups.models import Group, GroupMember
from publet.projects.models import (
    Publication, Type, Theme, Article,
    PhotoBlock, VideoBlock, Photo, Readability, TextBlock, Flavor,
    NewTheme, NewArticle
)
from publet.projects.api import (
    PhotoBlockResource, PhotoResource, ThemeResource, ArticleResource,
    TextBlockResource, GroupResource, ColorResource
)
from publet.projects import parse
from publet.projects.dateparse import find_dates
from publet.utils.fn import merge
from publet.utils.utils import int_to_string
from publet.users.models import PubletApiKey
from publet.projects.patch import validate_ops


def refresh(obj):
    if not obj.pk:
        raise Exception('no pk')

    return obj.__class__.objects.get(pk=obj.pk)


class ApiBaseTest(TestCase):

    def _get_header(self, response, name):
        return response._headers[name][1]

    def setUp(self):
        self.auth = dict(username='admin', password='admin')
        self.user = get_user_model().objects.create(
            username=self.auth['username'])
        self.user.is_superuser = False
        self.user.save()
        self.api_key = PubletApiKey.objects.get(user=self.user)
        self.client.login()

    def _login(self, obj=None):
        self.client.logout()
        auth = obj or self.auth
        assert self.client.login(**auth)

    def _call_api(self, method, path, data, user=None):
        meth = getattr(self.client, method)

        if method in "post put":
            data = json.dumps(data)

        content_type = "application/json"
        user = user or self.user
        username = user.username
        api_key = user.publet_api_key.key

        if 'api/2/' in path:
            from base64 import b64encode
            s = b64encode('{}:{}'.format(username, api_key))
            auth = 'Basic {}'.format(s)
        else:
            auth = 'ApiKey {}:{}'.format(username, api_key)

        return meth(path, data, content_type=content_type,
                    HTTP_AUTHORIZATION=auth,
                    HTTP_X_Accept="application/json",
                    HTTP_X_CONTENT_TYPE="application/json",
                    HTTP_Accept="application/json")

    def assertStatusCode(self, method, path, data, code, use_json=True,
                         user=None):

        response = self._call_api(method, path, data, user=user)

        if response.status_code != code:
            print response

        self.assertEqual(response.status_code, code)

        if use_json:
            try:
                response.data = json.loads(response.content)
            except:
                pass
        return response


class ArticleTest(ApiBaseTest):

    def test_filename_for_format(self):
        group = Group.objects.create(name='test')
        user = get_user_model().objects.create(username='test',
                                               email='test@test.com')

        GroupMember.objects.create(user=user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)

        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        renders_dir = os.path.join(settings.BASE_PATH, 'renders')
        last_modified = article.modified.strftime('%Y%m%d-%H%M%S')

        filename = '%s/%s/%s-%s.pdf' % (renders_dir, 'test', 'test',
                                        last_modified)
        # E.g.
        # /vagrant/publet/renders/test/test-20130903-093502.pdf

        self.assertEquals(filename, article.filename_for_format('pdf'))

    def test_delete_article(self):
        group = Group.objects.create(name='test')

        GroupMember.objects.create(user=self.user, group=group, role='O')
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)

        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        url = ArticleResource().get_resource_uri(article)
        self.assertStatusCode('delete', url, '', 204)


class BlockTest(ApiBaseTest):

    def test_crop_marks(self):
        # TODO: Fix this after new cropping mechanism has been decided
        return
        group = Group.objects.create(name='test')
        user = get_user_model().objects.create(username='test',
                                               email='test@test.com')

        GroupMember.objects.create(user=user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)
        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        pb = PhotoBlock(article=article)
        pb.image = 'abc'
        pb.save()

        self.assertEquals(pb.get_crop_marks(), None)

        pb.set_crop_marks(dict(x=10, y=5, x2=210, y2=15))
        pb.save()

        crop_dict = pb.get_crop_marks()

        self.assertEquals(crop_dict['x'], 10)
        self.assertEquals(crop_dict['y'], 5)
        self.assertEquals(crop_dict['x2'], 210)
        self.assertEquals(crop_dict['y2'], 15)

        args = parse_qs(urlparse(pb.cropped_image_url).query)
        crop = args['crop'][0]

        self.assertEquals(crop, "10,5,200,10")

    def test_video_types(self):
        vb = VideoBlock()
        vb.video_url = 'http://www.youtube.com/watch?v=_RwEk7JxQGY'

        self.assertEquals('youtube', vb.video_type)
        self.assertEquals('_RwEk7JxQGY', vb.video_id)
        self.assertEquals('_RwEk7JxQGY', vb.video_id)
        self.assertEquals('_RwEk7JxQGY', vb.video_id)

        vb.video_url = 'https://vimeo.com/123'

        self.assertEquals('vimeo', vb.video_type)
        self.assertEquals('123', vb.video_id)

        vb.video_url = 'https://abc.com'

        self.assertEquals(None, vb.video_type)
        self.assertEquals(None, vb.video_id)

    def test_flavor_resolution(self):
        group = Group.objects.create(name='test')
        user = get_user_model().objects.create(username='test',
                                               email='test@test.com')

        GroupMember.objects.create(user=user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')
        theme.create_defaults()

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)
        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        f = Flavor.objects.create(name='flavor', theme=theme, type='text',
                                  size=32, custom_css_classes='hello')

        tb = TextBlock.objects.create(article=article, content='Hello',
                                      flavor=f)

        tb.resolve()

        self.assertEquals(tb.size, 32)
        self.assertEquals(tb.custom_css_classes, 'hello')

        with self.assertRaises(AttributeError):
            tb.save()

        tb = refresh(tb)
        tb.size = 18
        tb.custom_css_classes = 'welp'

        tb.save()

        tb.resolve()
        self.assertEquals(tb.size, 18)
        self.assertEquals(tb.custom_css_classes, 'welp')

    def test_merge_fn(self):
        a = dict(c=1, d='', e=None, g=100)
        b = dict(c=2, e='e', f='x', g=None)

        r = merge(a, b)
        self.assertEquals(r['c'], 2)
        self.assertEquals(r['e'], 'e')
        self.assertEquals(r['f'], 'x')
        self.assertEquals(r['g'], 100)

    def test_locked(self):
        group = Group.objects.create(name='test')

        gm = GroupMember.objects.create(user=self.user, group=group, role='C')
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')
        theme.create_defaults()

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)
        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        tb = TextBlock(article=article, content='Hello', is_locked=True)
        tb.flavor = tb.get_default_flavor()
        tb.save()

        url = TextBlockResource().get_resource_uri(tb)
        data = {
            'content': 'hi',
            'resource_uri': url,
            'id': tb.id
        }

        tb_count = TextBlock.objects.all().count()
        self.assertStatusCode('put', url, data, 401)
        self.assertEquals(tb_count, TextBlock.objects.all().count())

        gm.role = 'O'
        gm.save()
        tb_count = TextBlock.objects.all().count()
        self.assertStatusCode('put', url, data, 200)
        self.assertEquals(tb_count, TextBlock.objects.all().count())

        tb = refresh(tb)
        self.assertEquals(tb.content, 'hi')


class PhotoTest(ApiBaseTest):

    def test_photo_create(self):
        group = Group.objects.create(name='test')

        GroupMember.objects.create(user=self.user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')
        theme = theme.create_defaults()

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)

        article = Article.objects.create(name='test', group=group,
                                         publication=publication)

        # --

        pb = PhotoBlock(article=article)
        pb.flavor = pb.get_default_flavor()
        pb.save()
        block_url = PhotoBlockResource().get_resource_uri(pb)

        data = {
            'block': block_url,
            'image': 'abc'
        }

        self.assertEquals(0, Photo.objects.count())

        self.assertStatusCode('post', PhotoResource().get_resource_uri(), data,
                              201)

        self.assertEquals(1, Photo.objects.count())


class ReadabilityTest(TestCase):

    HTML = """

<!doctype html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="description" content="Thoughts on web programming, open source hacking and the like. Honza Pokorny is a web developer in Halifax, Canada" >
  <meta name="viewport" content="width=550, maximum-scale=1.0" />
  <meta name="readability-verification" content="cXteMUVfc4F4DwUmDFS563269y9HLgfxK34fvdMC"/>
  fsdl ds 2013-12-02(9>>
  <<<<< 03#$@#$@fsdl ds 2013-12-2(9>>
  <<<<< 03#$@#$@fsdl ds 2013/12/2(9>>
  2/12/2013
  12/2/2013
  2.12.2013
  12.2.2013
  <title>Lisp parentheses - Honza Pokorny</title>
  <link rel="stylesheet" href="/media/screen.css" type="text/css" />
  <link rel="alternate" type="application/atom+xml" title="News-Feed" href="http://honza.ca/atom.xml" />
    <script type="text/javascript">
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', 'UA-4330851-12']);
        _gaq.push(['_trackPageview']);

        (function(){
         var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
         ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
         var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
        })();

    </script>

    <script type="text/javascript">
    /* <![CDATA[ */
        (function() {
            var s = document.createElement('script'), t = document.getElementsByTagName('script')[0];

            s.type = 'text/javascript';
            s.async = true;
            s.src = 'http://api.flattr.com/js/0.6/load.js?mode=auto'

            t.parentNode.insertBefore(s, t);
        })();
    /* ]]> */
    </script>

</head>
<body>

    <div id="wrap">
        <div id="banner" class="body">
            <h1><a href="/">Honza Pokorny</a></h1>
        </div>
        <p>Thoughts on web programming and the world of technology</p>


<p class="article_date date">
    December 2, 2013, reading time: about one minute
</p>

<div id="content">
    <div class="section" id="lisp-parentheses">
<h1>Lisp&nbsp;parentheses</h1>
<p>Perhaps the number one reason why people are afraid to try Lisp or don&#8217;t like
it is the huge amounts of parentheses cluttering up the code.  It&#8217;s said to be
hard to read the code when it&#8217;s full of&nbsp;parentheses.</p>
<p>Any experienced Lisp programmer will tell you that the parentheses disappear
fairly early on.  After a while, you hardly notice them as something annoying.
In fact, going back to C-family languages will make you feel like you need to
type all kinds of crazy&nbsp;punctuation.</p>
<p>While Clojure technically doesn&#8217;t use significant whitespace like Python, in
reality, careful identation is crucial to writing clear&nbsp;code.</p>
<div class="highlight"><pre><span class="p">(</span><span class="kd">defn </span><span class="nv">crop-photo</span> <span class="p">[</span><span class="nv">user</span> <span class="nv">photo</span><span class="p">]</span>
  <span class="p">(</span><span class="nb">when </span><span class="p">(</span><span class="nf">authenticated?</span> <span class="nv">user</span><span class="p">)</span>
    <span class="p">(</span><span class="nb">when </span><span class="p">(</span><span class="nf">admin?</span> <span class="nv">user</span><span class="p">)</span>
      <span class="p">(</span><span class="nf">crop</span> <span class="nv">photo</span><span class="p">))))</span>
</pre></div>
<p>In this snippet, there are four levels of indentation, four nested expressions.
It&#8217;s easy to quickly scan this function guess what it does.  When a user is
authenticated and when they are an admin, crop the photo.  If any of the
<tt class="docutils literal">when</tt> expressions return a <em>falsy</em> value, the whole function will return
<tt class="docutils literal">nil</tt>.  All of this is possible because Clojure uses prefix notation.  This
means that the first element in the <tt class="docutils literal"><span class="pre">(&#8230;)</span></tt> form is the name of the function.
Therefore, you only need to scan the beginnings of lines to see what functions
are being called.  Also, you never have to pay attention to closing parentheses
because they are all sitting together at the end of the&nbsp;function.</p>
<p>In Clojure, it&#8217;s also idiomatic to put function arguments on new lines and
align&nbsp;them.</p>
<div class="highlight"><pre><span class="p">(</span><span class="nb">or </span><span class="p">(</span><span class="nf">admin?</span> <span class="nv">user</span><span class="p">)</span>
    <span class="p">(</span><span class="nf">staff?</span> <span class="nv">user</span><span class="p">))</span>
</pre></div>
<p>In this example, the <tt class="docutils literal">or</tt> macro usually takes two arguments.  We put each
argument on its own line and align them.  This way it&#8217;s visually clear what the
code&nbsp;does.</p>
<p>Finally, when writing Clojure code, you rarely have to worry about matching up
your parentheses.  This is a job for your text editor.  Inserting a new
expression usually involves typing the <tt class="docutils literal">(</tt> key and having its friend <tt class="docutils literal">)</tt>
inserted for&nbsp;you.</p>
</div>

</div>

<span class="article_buttons">
    <script src="http://platform.twitter.com/widgets.js" type="text/javascript"></script>
    <a href="http://twitter.com/share" class="twitter-share-button"
        data-url="http://honza.ca/2013/12/lisp-parentheses"
        data-via="_honza"
        data-text="Lisp parentheses"
        data-count="none">Tweet</a>
    <a href="http://honza.ca/2013/12/lisp-parentheses"
        class="FlattrButton"
        rev="flattr;uid:honza;button:compact;"
        title="Lisp parentheses"
        style="display:none"></a>

</span>


    </div>

</body>
</html>
    """

    def test_parsing(self):
        doc = parse.parse_html(self.HTML)
        self.assertEquals(9, len(doc['paragraphs']))
        self.assertEquals('Lisp parentheses', doc['title'])

        dates = list(find_dates(self.HTML))
        self.assertEquals(8, len(dates))

        group = Group.objects.create(name='test')
        user = get_user_model().objects.create(username='test',
                                               email='test@test.com')

        GroupMember.objects.create(user=user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = Theme.objects.create(name='Default')
        theme.create_defaults()

        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)

        self.assertEquals(0, Article.objects.all().count())

        url = 'http://honza.ca/2013/12/lisp-parentheses'
        r = Readability.objects.create(url=url, publication=publication)
        r.parse(self.HTML)

        all_articles = Article.objects.all()

        # One for the Readability, one for the TOC
        self.assertEquals(2, all_articles.count())
        p = Publication.objects.get(pk=publication.pk)
        self.assertEquals(2, p.article_set.all().count())

        # Make sure all orders are unique
        self.assertEquals(2, len(set([a.order for a in all_articles])))

        # 9 paragraphs
        # one heading, one source, one date
        # one toc
        self.assertEquals(13, TextBlock.objects.all().count())

        self.assertEquals(1, Readability.objects.all().count())

        r = Readability.objects.all()[0]
        self.assertTrue(r.is_processed)

        toc_tb = TextBlock.objects.filter(article__is_toc=True)[0]
        self.assertTrue(url in toc_tb.content)

        toc = Article.objects.filter(is_toc=True)[0]
        self.assertEquals(toc.order, 1)

    def test_leading_sentences(self):
        text = 'Sentence 1. Sentence 2. Sentence 3. Abc'
        leading = Readability().get_leading_sentences(text, num=2)
        self.assertEquals(leading, 'Sentence 1. Sentence 2.')

    def test_format_date(self):
        f = Readability().format_date

        self.assertEquals('May 21, 2013',
                          f(dict(year='2013', month='5', day='21')))
        self.assertEquals('May 21, 2013',
                          f(dict(year='2013', month='21', day='5')))

        self.assertEquals('May 1, 2013',
                          f(dict(year='2013', month='5', day='1')))


class ThemeTest(ApiBaseTest):

    def test_default_fonts_api(self):
        group = Group.objects.create(name='test')
        GroupMember.objects.create(user=self.user, group=group, role='O')
        group_url = GroupResource().get_resource_uri(group)

        data = {
            'name': 'hi',
            'group': group_url
        }
        self.assertStatusCode('post', ThemeResource().get_resource_uri(), data,
                              201)
        self.assertEquals(2, Theme.objects.all().count())

        t = Theme.objects.all()[0]
        self.assertEquals(t.fonts.all().count(), 8)

    def test_copy_theme(self):
        group = Group.objects.create(name='test')
        new_group = Group.objects.create(name='new group')
        theme = Theme.objects.create(name='Panda', group=group)
        theme.create_defaults()

        original_count = Theme.objects.all().count()

        new_theme = theme.copy_to_group(new_group)

        self.assertEquals(original_count + 1, Theme.objects.all().count())

        new_group = refresh(new_group)
        group = refresh(group)

        self.assertEquals(new_group.theme_set.all().count(), 2)
        self.assertEquals(group.theme_set.all().count(), 2)

        new_fonts = [f.name for f in new_theme.fonts.all()]
        fonts = [f.name for f in theme.fonts.all()]
        self.assertEquals(set([]), set(new_fonts).difference(set(fonts)))

        new_colors = [f.hex for f in new_theme.get_colors().all()]
        colors = [f.hex for f in theme.get_colors().all()]
        self.assertEquals(set([]), set(new_colors).difference(set(colors)))

    def test_deleting_a_color(self):
        group = Group.objects.create(name='test')
        GroupMember.objects.create(user=self.user, group=group, role='O')
        theme = Theme.objects.create(name='Panda', group=group)
        theme.create_defaults()
        theme = refresh(theme)
        color_count = theme.get_colors().count()

        color_333 = theme.get_colors().get(hex='333333')

        pub_type = Type.objects.create(name='pub type')
        publication = Publication.objects.create(
            name='test',
            group=group,
            type=pub_type,
            theme=theme)

        article = Article.objects.create(name='test', group=group,
                                         publication=publication)
        f = Flavor.objects.create(name='flavor', theme=theme, type='text',
                                  size=32, custom_css_classes='hello',
                                  color=color_333)

        tb = TextBlock.objects.create(article=article, content='Hello',
                                      flavor=f, color=color_333)

        # Let's delete header color
        color_333_url = ColorResource().get_resource_uri(color_333)

        self.assertStatusCode('delete', color_333_url, None, 204)

        theme = refresh(theme)
        self.assertEquals(None, theme.header_color)
        self.assertEquals(color_count - 1, theme.get_colors().all().count())

        tb = refresh(tb)
        self.assertEquals(None, tb.color)

        f = refresh(f)
        self.assertEquals(None, f.color)


class JSONPatchTest(ApiBaseTest):

    def setUp(self):
        self.auth = dict(username='test', password='admin')
        self.user = get_user_model().objects.create(
            username=self.auth['username'])
        self.user.set_password(self.auth['password'])
        self.user.is_superuser = False
        self.user.save()
        self.api_key = PubletApiKey.objects.get(user=self.user)

        group = Group.objects.create(name='test')

        GroupMember.objects.create(user=self.user, group=group)
        pub_type = Type.objects.create(name='pub type')
        theme = NewTheme.objects.create(name='Default', group=group)

        self.publication = Publication.objects.create(
            new_style=True,
            name='test',
            group=group,
            type=pub_type,
            new_theme=theme)

        self.article = NewArticle.objects.create(name='test', order=0,
                                                 publication=self.publication,
                                                 created_by=self.user)
        NewArticle.objects.create(name='test 2', order=1,
                                  publication=self.publication,
                                  created_by=self.user)

        self.publication = refresh(self.publication)

    def test_simple(self):
        ops = [
            {
                'op': 'replace',
                'path': '/article/sections/0/bg/color',
                'value': 'blue'
            },
            {
                'op': 'replace',
                'path': '/article/sections/0/bg/color',
                'value': 'red'
            }
        ]

        article = refresh(self.article)
        article.update(ops)
        article = refresh(self.article)

        self.assertEquals(article.data['sections'][0]['bg']['color'], 'red')

    def test_invalid_payload(self):
        ops = [
            {
                'op': 'replace',
                'path': '/name',
                'value': 'Cool'
            },
            {
                'op': 'replace',
                'path': '/name',
                'value': 'Cool name'
            },
            {
                'op': 'replace',
                'path': '/sections/0/bg/color',
                'value': 'hi'
            }
        ]

        self.assertTrue(validate_ops(ops))
        self.assertFalse(validate_ops({}))
        self.assertFalse(validate_ops([{}]))

    def test_removing_section(self):
        self.assertEquals(2, NewArticle.objects.all().count())
        self.assertEquals(self.publication.articles().all().count(), 2)
        sec_len = len(self.article.data['sections'])

        ops = [
            {
                'op': 'remove',
                'path': '/article/sections/0',
            }
        ]

        self.article.update(ops)

        self.assertEquals(2, NewArticle.objects.all().count())
        self.assertEquals(self.publication.articles().all().count(), 2)

        article = refresh(self.article)
        self.assertEquals(sec_len - 1, len(article.data['sections']))

    def test_adding_article(self):
        url = '/api/2/publication/{}/articles/'.format(self.publication.pk)
        data = {
            'name': 'hi'
        }
        self.assertStatusCode('post', url, data, 201)

    def test_nav(self):
        ops = [
            {
                'op': 'replace',
                'path': '/publication/nav/textColor',
                'value': 'yo'
            }
        ]

        publication = refresh(self.publication)
        publication.update(ops)
        publication = refresh(self.publication)

        self.assertEquals(publication.nav['textColor'], 'yo')


class ValidationTest(TestCase):

    def test_int_to_string(self):
        self.assertEquals(int_to_string(-1), None)
        self.assertEquals(int_to_string(0), 'zero')
        self.assertEquals(int_to_string(1), 'one')
        self.assertEquals(int_to_string(2), 'two')
        self.assertEquals(int_to_string(22), 'twenty-two')
        self.assertEquals(int_to_string(100), None)
        self.assertEquals(int_to_string(1000), None)
        self.assertEquals(int_to_string(1.1), None)

    def test_theme(self):
        group = Group.objects.create(name='test')
        theme = NewTheme(name='theme', group=group)
        theme.save()
