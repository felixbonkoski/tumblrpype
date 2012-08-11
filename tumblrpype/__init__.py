# -*- coding: utf-8 -*-
"""
!    tumblrpype
!  --------------------------------------------------------------------------
!    
!    tumblrpype is a Python Page Editor for Tumblr.
!
!    It provides a simple tool for downloading and uploading your Custom
!    Theme HTML to and from Tumblr.  This allows you to skip the annoying
!    "copy - paste" routine that is usually a part of Tumblr development.
!
!    Except where otherwise noted, the code in tumblrpype is
!        Copyright (c) 2012  Felix Bonkoski <felix@post-theory.com>
!        Licensed under the MIT license:
!            <http://www.opensource.org/licenses/mit-license.php>
!
"""

__version_info__ = (0, 1, 0)
__version__ = '.'.join(map(str, __version_info__))
__author__ = "Felix Bonkoski <felix@post-theory.com>"
__copyright__ = "Copyright 2012, Felix Bonkoski"
__license__ = "MIT License"

__all__ = [ 'TumblrUser', 'TumblrLogin', 'FetchError', 'LoginError']

#-------------------------------------------------------------------------------

import os

from login import TumblrLogin, FetchError, LoginError
from user import TumblrUser
from config import _CONFIG_DIR

#-------------------------------------------------------------------------------

if not os.path.exists(_CONFIG_DIR):
    os.mkdir(_CONFIG_DIR)
else:
    if not os.path.isdir(_CONFIG_DIR):
        raise IOError('Could not use config directory: %s' % _CONFIG_DIR)

