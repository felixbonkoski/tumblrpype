# -*- coding: utf-8 -*-
"""
!    user.py
!  --------------------------------------------------------------------------
!    
!    Implements a TumblrUser object that encapsulates the login information,
!    as well as the cookies for that user.  Saves / reads the users from the
!    tumblrpype config directory.
!
!    Except where otherwise noted, the code in tumblrpype is
!        Copyright (c) 2012  Felix Bonkoski <felix@post-theory.com>
!        Licensed under the MIT license:
!            <http://www.opensource.org/licenses/mit-license.php>
!
"""

import os

from config import _CONFIG_DIR

__all__ = ['TumblrUser']

#-------------------------------------------------------------------------------

class TumblrUser(object):

    def __init__(self):
        self.login = None
        self.password = None
        self.blogname = None
        self.cookiesfile = None

    def __user_dir(self):
        return os.path.join(_CONFIG_DIR, self.blogname)
    def __user_cred_file(self):
        return os.path.join(self.__user_dir(), 'credentials')
    def __user_cookie_file(self):
        return os.path.join(self.__user_dir(), 'cookies')

    def create(self, login, password, blogname):
        self.login = login
        self.password = password
        self.blogname = blogname
        self.cookiesfile = self.__user_cookie_file()

        self.save()

    def save(self):

        config_user_dir = self.__user_dir()

        if not os.path.exists(config_user_dir):
            os.mkdir(config_user_dir)
        else:
            if not os.path.isdir(config_user_dir):
                raise IOError("Cannot create User Config directory at: %s" % config_user_dir)

        # create credentials file:
        config_user_cred = self.__user_cred_file()
        with open(config_user_cred, 'wb') as F:
            F.write('%s\n' % self.login)
            F.write('%s\n' % self.password)
            F.write('%s\n' % self.blogname)

        # create empty cookies file
        if not os.path.exists(self.cookiesfile):
            with open(self.cookiesfile, 'wb') as F:
                F.write("#LWP-Cookies-2.0\n")

    def load(self, blogname):
        # attempt to load from config dir

        self.blogname = blogname
        config_user_cred = self.__user_cred_file()

        if not os.path.exists(config_user_cred):
            raise IOError('User does not exist: %s' % config_user_cred)

        with open(config_user_cred, 'rb') as F:
            self.login = F.readline().strip()
            self.password = F.readline().strip()
            self.blogname = F.readline().strip()

        self.cookiesfile = self.__user_cookie_file()
