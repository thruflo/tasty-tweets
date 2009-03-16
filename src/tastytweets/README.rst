Usage
-----

Install it::

    $ easy_install tastytweets

Find all twitter users who've posted on the URLs you're interested in since you last
executed the script::

    $ ./path/to/bin/tastytweets-find -u USERNAME -p PASSWORD -k KEY

Or use it to find and automatically follow those users (if you're not following them
already)::

    $ ./path/to/bin/tastytweets-follow -u USERNAME -p PASSWORD -k KEY

To automate the script to check for new users to follow every 6 hours, run the following
and it'll set up the appropriate `crontab <http://en.wikipedia.org/wiki/Cron>`_ job for you::

    $ ./path/to/bin/tastytweets-automate -u USERNAME -p PASSWORD -k KEY

Twitter has a limit of 100 requests per hour, so the script also uses a directory queue to
store requests to make on the filesystem and adds a cronjob (for the duration of the queue
being full) to process one request every 3 minutes.

The script uses an internal ``status_id`` to filter tweets so only those tweets that were
made since the script was last run are picked up.  To reset the counter (to the first *eva*
tweet :p) run::

    $ ./path/to/bin/tastytweets-reset

You'll need a `Delicious <http://www.delicious.com>`_ account and a `Twitter <http://www.twitter.com>`_ account.  Plus you'll need a `Backtweet API <http://www.backtweet.com/api>`_ Key.

The default tag the script looks for in your delicious account is 'follow' but you can
pass any tags using the ``-t`` option, e.g.: ``-t foo bar dolores`` will only pick up urls
tagged with ``foo`` and ``bar`` and ``dolores``.


Notes
-----

- need to ensure that an error in the script doesn't leave unneccesary cronjobs running every 3 minutes ;)
- in fact, there's no real error handling for lost connections, etc. going on at all, except retrying the 'follow user' post
- cron output should be routed to a log file in ~/.tastytweets* somewhere
- the directory queue folders should be cleaned up from time to time
- needs some doc strings inc. tests