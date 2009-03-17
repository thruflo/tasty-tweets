
Overview
--------


This is a mashup that uses three APIs:

- `Delicious feeds <http://delicious.com/help/feeds>`_

- `Backtweets API <http://backtweets.com/api>`_

- (optionally) `Twitter API <http://apiwiki.twitter.com/REST+API+Documentation>`_


It works as follows:

#. fetch a list of urls tagged on delicious (which whatever tag(s) you specify)

#. query backtweets to find users who've posted links to those urls

#. return a list of those users' twitter usernames


If you want, you can:

#. either just find the usernames; or

#. automatically start following the users you find on twitter


If you really like the idea, you can automate the script to check for new users
to follow every few hours (the delay is configurable).

The idea is that you can find people who are interested in sites you're interested
in. If you find that by automatically following them they happen to follow you
back, well, who knows, maybe this little package will make you famous ;)

How useful it is will depend on the sites you tag.  Having ``http://www.yahoo.com``
in there is not likely to be much of a useful filter.  Wheras having something
specialist like, say, http://tav.espians.com, probably will be.



Prerequisites
-------------


- you'll need a unix based computer atm; this is due to the ``python-crontab``
  dependency which we're using to schedule tasks.  There are many others ways of
  scheduling tasks, if you'd like to improve the package and make it windows
  compatible, please `go ahead <http://github.com/thruflo/tasty-tweets>`_ ;)

- you need `Python <http://www.python.org>`_

- you'll need a `Delicious <http://www.delicious.com>`_ account

- you'll need a `Backtweets <http://www.backtweet.com/api>`_ API key

- if you want to automatically follow the users you'll need a
  `Twitter <http://www.twitter.com>`_ account



Usage
-----


Install it::

    $ easy_install tastytweets

This installs a number of console scripts (it'll put them where your python puts
scripts). To find all twitter users who've posted on the URLs you're
interested in::

    $ ./path/to/bin/tastytweets-find [... options ...]

``tastytweets-find`` is the simplest way of using this package, especially if
you don't like the way the automation that follows has been implemented.

Find and automatically follow those users (in real life on your twitter account, for real,
don't do this unless you actually mean to!!)::

    $ ./path/to/bin/tastytweets-follow [... options ...]

Automate the script (to run forever) to check for new users to follow every
6 hours::

    $ ./path/to/bin/tastytweets-automate [... options ...] --follow-delay 6

The command line options required vary according to what you're trying to do.
To see all the options, run one of the scripts with the ``-h`` option::

    $ ./path/to/bin/tastytweets-find -h

The default tag the script looks for in your delicious account is 'follow' but
you can pass any tags using the ``-t`` option, e.g.: ``-t foo bar dolores``
will only pick up urls tagged with ``foo`` and ``bar`` and ``dolores`` (n.b.: it's
cumulative, like ``'foo' AND 'bar' AND 'dolores'``).

For example, a fully optioned-up call might be [line wraps are marked ``\``]::

    $ ./path/to/bin/tastytweets-automate -u TWITTER_USERNAME -p TWITTER_PASSWORD \
    -k BACKTWEETS_KEY -d DELICIOUS_USER -t follow socialgraphing \
    --follow-delay 6 --push-delay 5

There are two implementation details you should be aware of.  Firstly, Twitter
has a limit of 100 requests per hour, so the script also uses a directory queue
to store requests to make on the filesystem and adds a cronjob (for the duration
of the queue being full) to process one request every ``--push-delay`` minutes.  
This defaults to every 5 minutes.

Secondly, the package is designed primarily to be automated, so it maintains an
internal record of the last time it checked for posts.  If you want to use the
``./tastytweets-find`` or ``./tastytweets-follow`` scripts manually, you may want
to reset the internal record so that you get all of the posts.

To reset the last time checked::

    $ ./path/to/bin/tastytweets-reset-status-id

To reset the last time-checked, reset the queue, destroying any pending requests
and delete any crontab jobs scheduled::

    $ ./path/to/bin/tastytweets-reset-everything

To manually push queued follow requests use::

    $ ./path/to/bin/tastytweets-push

You shouldn't need to though, as ``tastytweets-follow`` takes care of pushing
automatically.

Finally, you can also, of course, use the package directly from python.  See
``tastytweets.client.TastyTweeter.__doc__`` for details.