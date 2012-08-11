# -*- coding: utf-8 -*-
"""
!    config.py
!  --------------------------------------------------------------------------
!    
!    Just some global Config directives
!
!    Except where otherwise noted, the code in tumblrpype is
!        Copyright (c) 2012  Felix Bonkoski <felix@post-theory.com>
!        Licensed under the MIT license:
!            <http://www.opensource.org/licenses/mit-license.php>
!
"""
import os
import sys

_DEFAULT_CONFIG_DIR = os.path.expanduser("~/.tumblrpype")

_CONFIG_DIR = _DEFAULT_CONFIG_DIR

DEBUG = True

def debug(s):
    if DEBUG:
        sys.stderr.write('%s\n' % s)
