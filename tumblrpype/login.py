# -*- coding: utf-8 -*-
"""
!    login.py
!  --------------------------------------------------------------------------
!    
!    This module implements logging into Tumblr, and fetching various pages
!    in meaningful ways.
!
!    Except where otherwise noted, the code in tumblrpype is
!        Copyright (c) 2012  Felix Bonkoski <felix@post-theory.com>
!        Licensed under the MIT license:
!            <http://www.opensource.org/licenses/mit-license.php>
!
"""

import urllib2
import cookielib
import re
import jsonlib
import os

from bs4 import BeautifulSoup #, Tag

from formdata import encode_multipart_formdata, encode_urlencoded_formdata
from config import _CONFIG_DIR, DEBUG, debug
from user import TumblrUser

__all__ = ['FetchError', 'LoginError', 'TumblrLogin']

#-------------------------------------------------------------------------------

class FetchError(Exception): pass
class LoginError(Exception): pass

class HTTPFileCookieProcessor(urllib2.BaseHandler):
    def __init__(self, cookieFile):
        self.cookiejar = cookielib.LWPCookieJar(cookieFile)

    def http_request(self, request):
        self.cookiejar.add_cookie_header(request)
        return request

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        return response

    https_request = http_request
    https_response = http_response

class HTTPPostHandler(urllib2.BaseHandler):
    def __init__(self, contentType):
        self.contentType = contentType

    def http_request(self, request):
        request.add_unredirected_header('Content-type', self.contentType)
        return request

    https_request = http_request


class TumblrLogin(object):

    def __init__(self, login, password = None, blogname = None, cookiesfile = None, **kwargs):

        if isinstance(login, TumblrUser):
            self.login = login.login
            self.password = login.password
            self.blogname = login.blogname
            cookiesfile = login.cookiesfile
        else:
            self.login = login
            self.password = password
            self.blogname = blogname

        if cookiesfile is None:
            cookiesfile = os.path.join(_CONFIG_DIR, 'cookies-%s.tmp' % blogname)

        self.cookieHandler = HTTPFileCookieProcessor(cookiesfile)
        self.cookieJar = self.cookieHandler.cookiejar
        self.cookieFile = self.cookieJar.filename

        self.load_cookies()

        self.logged_in = False
        self._login()

    def save_cookies(self):
        self.cookieJar.save(ignore_discard = True, ignore_expires = True)

    def load_cookies(self):
        if os.path.exists(self.cookieFile):
            self.cookieJar.load(ignore_discard = True, ignore_expires = True)

    def _make_opener(self):

        opener = urllib2.build_opener(self.cookieHandler)

        opener.addheaders = [('User-agent', 'tumblrpype/0.1')]

        return opener

    def _login(self):

        debug("Logging in [%s / %s]" % (self.login, self.blogname))

        opener = self._make_opener()

        # If we have cookies, let's see if we are logged in:
        if len(self.cookieJar):
            debug("  >> Testing cookies...")

            resp0 = opener.open('https://www.tumblr.com')
            if resp0.code != 200:
                debug("  !! Failed to fetch '/': Error [%s]" % resp0.code)
                raise LoginError('Could not fetch www.tumblr.com')


            html0 = resp0.fp.read()
            if 'id="logged_in"' in html0 and not 'id="logged_out"' in html0:
                debug("  <3 Good - already logged in.")
                self.logged_in = True

        if not self.logged_in:
            debug("  >> Fetching /login Page...")

            # OK, we need to login, Fetch the login page first
            resp1 = opener.open('https://www.tumblr.com/login')
            if resp1.code != 200:
                debug("  !! Failed to fetch '/login': Error [%s]" % resp1.code)
                raise LoginError('Could not fetch www.tumblr.com/login')

            debug("  >> Sending Login info...")

            # login is POSTed with Mime-Type 'application/x-www-form-urlencoded'
            loginInfo = {'user[email]' : self.login,
                         'user[password]' : self.password }
            loginInfo = encode_urlencoded_formdata(loginInfo)

            #origHeaders = [h for h in opener.addheaders]

            opener2 = self._make_opener()
            opener2.addheaders.append(('Content-Type', 'application/x-www-form-urlencoded'))

            resp2 = opener2.open('https://www.tumblr.com/login', data = loginInfo)
            html2 = resp2.fp.read()

            #opener.addheaders = origHeaders

            # Some hacky heuristics to determine if the login was a Success
            codeOK = resp2.code == 200
            hasRefresh = '<meta http-equiv="Refresh" content="0;url=/dashboard">' in html2
            hasNoErrors = 'SignupProcess.errors =' not in html2

            if codeOK and hasRefresh and hasNoErrors:
                debug("  <3 Success - logged in.")

            else:
                debug("  !! Login Failed: Error [%s]" % resp2.code)
                raise LoginError('Login failed')

        #//end if

        self.save_cookies()
        self.logged_in = True
        return True

    def fetch(self, uriFrag):

        debug("Fetching www.tumblr.com/%s" % uriFrag)

        opener = self._make_opener()
        resp = opener.open('http://www.tumblr.com/%s' % uriFrag)
        if resp.code != 200:
            debug("  !! Failed to fetch: Error [%s]" % (resp.code))
            return None

        html = resp.fp.read()

        return html

    def __get_customize_page(self):

        debug("Fetching Customize Page [%s]" % self.blogname)

        opener = self._make_opener()
        resp = opener.open('http://www.tumblr.com/customize/%s' % self.blogname)
        if resp.code != 200:
            debug("  !! Failed to fetch '/customize/%s': Error [%s]" % (self.blogname, resp.code))
            return None

        html = resp.fp.read()

        # find the "user_form_key"
        m = re.search(r'Tumblr\.Customize\.user_form_key\s?=\s?[\'\"]([^\'\"]+)[\'\"];', html)
        if not m:
            debug("  !! Failed to parse Theme: Could not find [user_form_key]")
            return None

        userFormKey = m.group(1)

        m = re.search(r'Tumblr\.Customize\.blog\.set\((.+)(?=\);\n)', html)
        if not m:
            debug("  !! Failed to parse Theme: Could not find JSON object in Tumblr.Customize.blog.set()")
            return None

        themeInfo = m.group(1)
        themeInfo = jsonlib.loads(themeInfo)

        themeInfo['user_form_key'] = userFormKey
        themeInfo['id'] = themeInfo['name']

        debug('  <3 Theme parsed')

        return themeInfo

    def __save_customize_page(self, themeInfo):

        # HTTP Post is done with Mime-type 'application/json'

        postData = jsonlib.dumps(themeInfo)

        postHandler = HTTPPostHandler('application/json')

        debug("Editing Theme HTML...")

        opener = self._make_opener()
        opener.add_handler(postHandler)
        opener.addheaders.append(('Referer', 'http://www.tumblr.com/customize/%s' % self.blogname))
        opener.addheaders.append(('Accept', 'application/json, text/javascript, */*; q=0.01'))
        opener.addheaders.append(('Accept-Charset', 'UTF-8,*;q=0.5'))
        opener.addheaders.append(('X-Requested-With', 'XMLHttpRequest'))
        opener.addheaders.append(('Origin', 'http://www.tumblr.com'))
        opener.addheaders.append(('Pragma', 'no-cache'))
        opener.addheaders.append(('Cache-Control', 'no-cache'))

        try:
            resp = opener.open('http://www.tumblr.com/customize_api/blog/%s' % self.blogname, data = postData)

        except Exception as e:
            debug("  !! Failed to edit HTML")
            return None

        newThemeInfo = resp.fp.read()
        newThemeInfo = jsonlib.loads(newThemeInfo)

        debug("  <3 Theme Saved.")

        return newThemeInfo

    def save_theme_html(self, newHTML):

        # first we have to retrieve the customize page, to get the object that describes
        # all of the settings on the theme.

        self.load_cookies()

        themeInfo = self.__get_customize_page()
        if not themeInfo:
            return False

        themeInfo['custom_theme'] = newHTML.decode('utf-8')

        ret = self.__save_customize_page(themeInfo)

        return ret

    def get_theme_html(self):

        themeInfo = self.__get_customize_page()
        if not themeInfo:
            return None

        return themeInfo['custom_theme']

    def __mark_photo_private(self, postID, editPage):

        debug('  >> Parsing Edit Page')
        soup = BeautifulSoup(editPage)

        form = {}

        # Build caption
        m = re.search(r'<textarea.*?id="post_two".*?>(.*?)</textarea>', editPage, re.I | re.M | re.DOTALL)
        if not m:
            debug('  !! Couldn\'t find caption!')
            return

        caption = m.group(1)
        caption = re.sub('&lt;', '<', caption)
        caption = re.sub('&gt;', '>', caption)
        caption = re.sub('&amp;', '&', caption)
        caption = re.sub('&#13;', '\r', caption)

        # Build the form data for posting
        form['UPLOAD_IDENTIFIER'] = soup.select('#upload_id')[0]['value']
        form['post[state]'] = 'private'
        form['post[publish_on]'] = ''
        form['post[draft_status]'] = ''
        form['post[date]'] = soup.select('#post_date')[0].get('value') or ''
        form['post[source_url]'] = soup.select('#post_source_url')[0].get('value') or ''
        form['post[tags]'] = soup.select('#post_tags')[0].get('value') or ''
        form['post[slug]'] = ''
        form['custom_tweet'] = 'Photo: [URL]'
        form['custom_tweet_changed'] = '0'
        form['is_rich_text[one]'] = '0'
        form['is_rich_text[two]'] = '1'
        form['is_rich_text[three]'] = '0'
        form['form_key'] = soup.select('#form_key')[0]['value']
        form['photo_raw'] = ''
        form['images'] = ('', '')
        form['photo_src'] = ''
        form['MAX_FILE_SIZE'] = '10485760'
        form['post[two]'] = caption
        form['post[three]'] = soup.select('#post_three')[0].get('value') or ''
        form['post[type]'] = 'photo'
        form['post[id]'] = str(postID)
        form['post[promotion_data][message]'] = '(No message)'
        form['post[promotion_data][icon]'] = '/images/highlighted_posts/icons/bolt_white.png'
        form['post[promotion_data][color]'] = '#bb3434'

        postData = encode_multipart_formdata(form)

        multipartHandler = HTTPPostHandler(postData[1])

        debug("  >> Editing post to 'Private'")

        opener = self._make_opener()
        opener.add_handler(multipartHandler)
        opener.addheaders.append(('Referer', 'http://www.tumblr.com/edit/%s' % postID))
        opener.addheaders.append(('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'))
        opener.addheaders.append(('Accept-Charset', 'UTF-8,*;q=0.5'))

        resp = opener.open('http://www.tumblr.com/edit/%s' % postID, data = postData[0])
        html = resp.fp.read()

        # hacky heuristic:
        # After a successful edit, we should be returned to the Dashboard
        if '<body id="dashboard_index"' in html:
            debug('  >> Success!')
            return True
        else:
            debug('  !! Failed! Something went wrong!')
            return False

    def mark_post_private(self, postID, **kwargs):

        uriFrag = 'edit/%s' % postID

        editPage = self.fetch(uriFrag)
        if not editPage:
            raise FetchError('Failed to fetch www.tumblr.com/%s' % uriFrag)

        # Find out about this post, namely the Post Type
        soup = BeautifulSoup(editPage)

        Tpost_type = soup.select('#post_type')[0]
        postType = Tpost_type['value']

        if postType == 'photo':
            return self.__mark_photo_private(postID, editPage)
        else:
            raise NotImplementedError()


#//end class TumblrLogin
