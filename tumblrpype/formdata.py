# -*- coding: utf-8 -*-
"""
!    formdata.py  (tumblrpype)
!  --------------------------------------------------------------------------
!    
!    This module implements encoding of POST form data, for these Content-Types:
!
!        1. multipart/form-data
!        2. application/x-www-form-urlencoded
!
"""

import urllib
import codecs
import mimetypes
from uuid import uuid4
from io import BytesIO
import six
from six import b

writer = codecs.lookup('utf-8')[3]

#----------------------------------------------------------------------------------------------------------------------
#   These functions are taken from the Python urllib3 library, 'filepost.py'
#       https://github.com/shazow/urllib3
#   Copyright 2008-2012 Andrey Petrov and contributors
#       Licensed under the MIT License

def choose_boundary():
    """
    Our embarassingly-simple replacement for mimetools.choose_boundary.
    """
    return uuid4().hex


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def iter_fields(fields):
    """
    Iterate over fields.

    Supports list of (k, v) tuples and dicts.
    """
    if isinstance(fields, dict):
        return ((k, v) for k, v in six.iteritems(fields))

    return ((k, v) for k, v in fields)


def encode_multipart_formdata(fields, boundary = None):
    """
    Encode a dictionary of ``fields`` using the multipart/form-data mime format.

    :param fields:
        Dictionary of fields or list of (key, value) field tuples.  The key is
        treated as the field name, and the value as the body of the form-data
        bytes. If the value is a tuple of two elements, then the first element
        is treated as the filename of the form-data section.

        Field names and filenames must be unicode.

    :param boundary:
        If not specified, then a random boundary will be generated using
        :func:`mimetools.choose_boundary`.
    """
    body = BytesIO()
    if boundary is None:
        boundary = choose_boundary()

    for fieldname, value in iter_fields(fields):
        body.write(b('--%s\r\n' % (boundary)))

        if isinstance(value, tuple):
            filename, data = value
            writer(body).write('Content-Disposition: form-data; name="%s"; '
                               'filename="%s"\r\n' % (fieldname, filename))
            body.write(b('Content-Type: %s\r\n\r\n' %
                       (get_content_type(filename))))
        else:
            data = value
            writer(body).write('Content-Disposition: form-data; name="%s"\r\n\r\n'
                               % (fieldname))
            #body.write(b'Content-Type: text/plain\r\n\r\n')
            #body.write(b'\r\n')

        if isinstance(data, int):
            data = str(data)  # Backwards compatibility

        if isinstance(data, six.text_type):
            writer(body).write(data)
        else:
            body.write(data)

        body.write(b'\r\n')

    body.write(b('--%s--\r\n' % (boundary)))

    content_type = b('multipart/form-data; boundary=%s' % boundary)

    return body.getvalue(), content_type



#----------------------------------------------------------------------------------------------------------------------
#   These functions are taken from the Python oauth2 library
#       http://github.com/simplegeo/python-oauth2/
#   Copyright (c) 2007-2010 Leah Culver, Joe Stump, Mark Paschal, Vic Fryzel
#       Licensed under the MIT License



def to_unicode(s):
    if not isinstance(s, unicode):
        if not isinstance(s, str):
            raise TypeError('You are required to pass either unicode or string here, not: %r (%s)' % (type(s), s))
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError, le:
            raise TypeError("You are required to pass either a unicode object or a utf-8 string here. " +
                            "You passed a Python string object which contained non-utf-8: %r. " % s +
                            "The UnicodeDecodeError that resulted from attempting to interpret it as utf-8 was: %s" % le)
    return s

def to_utf8(s):
    return to_unicode(s).encode('utf-8')
def to_utf8_if_string(s):
    return to_utf8(s) if isinstance(s, basestring) else s
def to_utf8_optional_iterator(x):
    if isinstance(x, basestring):
        return to_utf8(x)
    try:
        l = list(x)
    except TypeError, e:
        assert 'is not iterable' in str(e)
        return x
    else:
        return [ to_utf8_if_string(e) for e in l ]

def encode_urlencoded_formdata(kvDict):
    """Serialize as post data for a POST request."""
    d = {}
    for k, v in kvDict.iteritems():
        d[k.encode('utf-8')] = to_utf8_optional_iterator(v)
    return urllib.urlencode(d, True).replace('+', '%20')
