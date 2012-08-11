from distutils.core import setup

setup(name = 'tumblrpype',
      author = 'Felix Bonkoski',
      author_email = 'felix@post-theory.com',
      version = '0.1.0',
      license = 'MIT',
      url = 'https://github.com/felixbonkoski/tumblrpype',
      description = 'tumblrpype is a Python Page Editor tool for Tumblr',
      requires = ['jsonlib', 'bs4', 'six'],
      packages = ['tumblrpype'],
      scripts = ['bin/tumblrpype.py']
      )
