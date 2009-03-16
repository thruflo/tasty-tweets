import base64
import crontab
import os
import pickle
import shutil
import sys
import time
import urllib
import urllib2

try:
    import json
except ImportError:
    import simplejson as json

from datetime import datetime

from directory_queue.directory_queue import DirectoryQueue
from directory_queue.generic_queue_item import GenericQueueItem


BACKTWEETS_URL = u'http://backtweets.com/search.json'

DELICIOUS_URL = u'http://feeds.delicious.com/v2/json/%s/%s?count=100'

TWITTER_FOLLOWING_URL = u'https://twitter.com/friends/ids/%s.json'
TWITTER_FOLLOW_URL = u'http://twitter.com/friendships/create/%s.json?follow=true'

STATUS_DATA = os.path.expanduser(
    '~/.tastytweets-statusdata.pkl'
)

QUEUE_DIR = os.path.expanduser(
    '~/.tastytweets-queue'
)


class TastyTweeter(object):
    status_ids = {}
    
    def _update_status_id(self):
        if not os.path.exists(self.status_data_path):
            self._init_status_id()
        sock = open(self.status_data_path, 'r')
        self.status_ids = pickle.load(sock)
        self.status_ids['previous'] = self.status_ids['current']
        sock.close()
    
    def _commit_status_id(self):
        sock = open(self.status_data_path, 'w')
        pickle.dump(self.status_ids, sock)
        sock.close()
    
    def _init_status_id(self):
        sock = open(self.status_data_path, 'w')
        self.status_ids = {'current': 0}
        self.status_ids = pickle.dump(self.status_ids, sock)
        sock.close()
    
    
    def _make_request(self, url, method, headers):
        headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-GB; rv:1.9.0.7) Gecko/2009021906 Firefox/3.0.7')
        if method == 'POST':
            data = urllib.urlencode({'foo': 'bar'})
            request = urllib2.Request(url, data=data, headers=headers)
        else:
            request = urllib2.Request(url, headers=headers)
        return request
    
    def _send_request(self, request):
        return urllib2.urlopen(request)
    
    def _request(self, url, method='GET', headers={}):
        request = self._make_request(url, method, headers)
        return self._send_request(request)
    
    
    def get_existing_users(self, user, password):
        url = TWITTER_FOLLOWING_URL % user
        sock = self._request(url, headers=self.auth_header)
        return json.load(sock)
    
    def get_sites(self, user, tags):
        url = DELICIOUS_URL % (
            user,
            tags
        )
        sock = self._request(url)
        results = json.load(sock)
        for item in results:
            yield item['u']
        
    
    def get_users_for_site(self, url):
        params = {
            'q': url,
            'since_id': self.status_ids['previous'],
            'key': self.backtweets_key,
            'itemsperpage': 100
        }
        url = '%s?%s' % (
            BACKTWEETS_URL,
            urllib.urlencode(params)
        )
        sock = self._request(url)
        data = json.load(sock)
        # the first tweet is the latest (Baby I know ... ;)
        if len(data['tweets']):
            latest = data['tweets'][0]
            if latest['tweet_id'] > self.status_ids['current']:
                self.status_ids['current'] = latest['tweet_id']
        for item in data['tweets']:
            yield item
        
    
    
    def reset(self):
        """
          
          Reset the latest tweet status id - thus scraping all the
          users from way back - and reset the follow queue.
          
          
        """
        self._init_status_id()
        shutil.rmtree(self.queue_dir)
    
    
    def find(self):
        """
          
          Returns a list of all users who've posted the url of a tagged site
          since the last check.
          
          
        """
        
        # update the last-checked-tweet status id
        self._update_status_id()
        
        # get the tagged urls
        self.urls = self.get_sites(self.delicious_user, self.tags)
        
        # we build a list of dicovered users
        discovered_users = []
        
        # for each tagged site
        for url in self.urls:
            # find the twitter users who's posted the url
            site_users = self.get_users_for_site(url)
            for user in site_users:
                username = user['tweet_from_user'].lower()
                if not username in discovered_users:
                    discovered_users.append(username)
                
            
        # store the updated status id
        self._commit_status_id()
        
        # return the list
        discovered_users.sort()
        return discovered_users
    
    def follow(self):
        """
          
          Finds all users who've posted the url of a tagged site since the
          last check and starts following them, iff not already following
          them.
          
          Returns a list of usernames.
          
          
        """
        
        # update the last-checked-tweet status id
        self._update_status_id()
        
        # get the tagged urls
        self.urls = self.get_sites(self.delicious_user, self.tags)
        
        # accessing twitter needs https auth, which we do with a simple header
        raw = "%s:%s" % (self.twitter_user, self.twitter_pwd)
        auth = base64.encodestring(raw).strip()
        self.auth_header = {'AUTHORIZATION': 'Basic %s' % auth}
        
        # get existing users
        self.existing_users = [] # self.get_existing_users(self.twitter_user, self.twitter_pwd)
        print 'TODO: actually call get_existing_users'
        
        # we build a list of new users
        following = []
        
        # for each tagged site
        for url in self.urls:
            # find the twitter users who's posted the url
            site_users = self.get_users_for_site(url)
            for user in site_users:
                userid = user['tweet_from_user_id']
                if not userid in self.existing_users:
                    username = user['tweet_from_user'].lower()
                    self.existing_users.append(userid)
                    request = self._make_request(
                        TWITTER_FOLLOW_URL % user, 
                        'POST',
                        self.auth_header
                    )
                    queue_item = self.queue.newQueueItem(username)
                    sock = open(queue_item.dataFileName(), 'w')
                    pickle.dump({
                            'errors': 0, 
                            'request': request
                        }, 
                        sock
                    )
                    sock.close()
                    self.queue.itemReady(queue_item)
                    following.append(username)
                
            
        # store the updated status id
        self._commit_status_id()
        
        # return the list
        following.sort()
        return following
        
        
    
    
    def push(self):
        queue_item = self.queue.getNext()
        if queue_item:
            sock = open(queue_item.dataFileName(), 'r')
            data = pickle.load(sock)
            sock.close()
            try:
                print 'TODO: actually _send_request'
                # self._send_request(data['request'])
                self.queue.itemDone(queue_item)
                return 'push: OK'
            except IOError:
                if data['errors'] < 3:
                    data['errors'] += 1
                    sock = open(queue_item.dataFileName(), 'w')
                    pickle.dump(data, sock)
                    sock.close()
                    self.queue.itemRequeue(queue_item)
                    return 'push: Requeue'
                else:
                    self.queue.itemError(queue_item)
                    return 'push: Error'
        return None
    
    
    def __init__(self, twitter_user='', twitter_pwd='', backtweets_key='', delicious_user=None, tags=['follow'], status_data=STATUS_DATA, queue_dir=QUEUE_DIR):
        # store the init params
        self.twitter_user = twitter_user
        self.twitter_pwd = twitter_pwd
        self.backtweets_key = backtweets_key
        self.delicious_user = delicious_user and delicious_user or twitter_user
        self.tags = '+'.join(tags)
        self.status_data_path = status_data
        self.queue_dir = queue_dir
        
        # init the queue
        if not os.path.exists(self.queue_dir):
            os.mkdir(self.queue_dir)
        self.queue = DirectoryQueue(self.queue_dir, GenericQueueItem)
    


def parse_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option(
        "-u", "--twitter-username", dest="twitter_user", default=None
    )
    parser.add_option(
        "-p", "--twitter-password", dest="twitter_pwd", default=None
    )
    parser.add_option(
        "-k", "--backtweets-key", dest="backtweets_key", default=None,
        help="see http://backtweets.com/api"
    )
    parser.add_option(
        "-d", "--delicious-username", dest="delicious_user", default=None
    )
    parser.add_option(
        "-t", "--delicious-tags", type="string", dest="tags", default='follow',
        help="seperate by a single space, i.e.: 'foo bar dolores' becomes ['foo', 'bar', 'dolores']"
    )
    parser.add_option(
        "-s", "--status-data-path", type="string", dest="status_data", default=STATUS_DATA,
        help="full path to the file where you want to store the status data, defaults to ~/.tastytweets-statusdata.pkl"
    )
    parser.add_option(
        "-q", "--queue-directory-path", type="string", dest="queue_dir", default=QUEUE_DIR,
        help="full path to the queue where you want to store the follow request job items, defaults to ~/.tastytweets-queue"
    )
    (options, args) = parser.parse_args()
    return options


def find():
    options = parse_options()
    if not options.backtweets_key:
        raise Exception('You must provide a http://backtweets.com/api key, i.e.: -k KEY')
    if not options.delicious_user:
        if not options.twitter_user:
            raise Exception('You must provide a delicious username, i.e.: -d mydelicioususername')
        else:
            options.delicious_user = options.twitter_user
    tt = TastyTweeter(
        backtweets_key = options.backtweets_key,
        delicious_user = options.delicious_user,
        tags = options.tags.split(' '),
        status_data = options.status_data,
        queue_dir = options.queue_dir
    )
    return tt.find()


def follow():
    print 'client.follow()'
    options = parse_options()
    if not options.backtweets_key:
        raise Exception('You must provide a http://backtweets.com/api key, i.e.: -k KEY')
    if not options.twitter_user:
        raise Exception('You must provide a twitter username, i.e.: -u mytwitterusername')
    if not options.twitter_pwd:
        raise Exception('You must provide a twitter password, i.e.: -p mytwitterpassword')
    tt = TastyTweeter(
        twitter_user = options.twitter_user,
        twitter_pwd = options.twitter_pwd,
        backtweets_key = options.backtweets_key,
        delicious_user = options.delicious_user,
        tags = options.tags.split(' '),
        status_data = options.status_data,
        queue_dir = options.queue_dir
    )
    following = tt.follow()
    # if we picked up any users
    if following:
        # then start pushing them to twitter
        push()
    return following


def push():
    print 'client.push()'
    # try to push a request up to twitter
    options = parse_options()
    tt = TastyTweeter(queue_dir = options.queue_dir)
    response = tt.push()
    # update the user's crontab according to the response:
    tab = crontab.CronTab()
    absolute_path_to_bin_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
    push = os.path.join(absolute_path_to_bin_folder, 'tastytweets-push')
    # is there's a response but not a cron job
    if response is not None and not tab.find_command(push):
        print 'setting push crontab'
        # then push every 3 minutes - adds 20 follows per hour
        cmd = '%s %s' % (
            push, 
            ' '.join(
                sys.argv[1:]
            )
        )
        cron = tab.new(command=cmd)
        cron.minute().every(1)
        print unicode(tab.render())
        tab.write()
    # else if there isn't a response (which means there's nothing in
    # the queue) and there is a cronjob running
    elif response is None and tab.find_command('tastytweets-push'):
        print 'removing push crontab'
        tab.remove_all(push)
        print unicode(tab.render())
        tab.write()
    return response


def reset():
    options = parse_options()
    tt = TastyTweeter(queue_dir = options.queue_dir)
    return tt.reset()


def automate():
    options = parse_options()
    if not options.backtweets_key:
        raise Exception('You must provide a http://backtweets.com/api key, i.e.: -k KEY')
    if not options.twitter_user:
        raise Exception('You must provide a twitter username, i.e.: -u mytwitterusername')
    if not options.twitter_pwd:
        raise Exception('You must provide a twitter password, i.e.: -p mytwitterpassword')
    # great trick to get the full path to the current console script's directory
    # see: http://www.faqs.org/docs/diveintopython/regression_path.html
    absolute_path_to_bin_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
    follow_script = os.path.join(absolute_path_to_bin_folder, 'tastytweets-follow')
    push_script = os.path.join(absolute_path_to_bin_folder, 'tastytweets-push')
    if crontab is not None:
        tab = crontab.CronTab()
        # remove existing
        tab.remove_all(follow_script)
        tab.remove_all(push_script)
        # follow every 6 hours
        cmd = '%s %s' % (
            follow_script, 
            ' '.join(
                sys.argv[1:]
            )
        )
        cron = tab.new(command=cmd)
        cron.hour().every(6)
        print unicode(tab.render())
        tab.write()
    return follow()

