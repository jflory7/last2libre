import json
import time

from urllib.parse import urlencode
from urllib.request import Request, URLError, HTTPError, urlopen


class ScrobbleException(Exception):
    pass


class InvalidScrobbleServer(Exception):
    pass


class ScrobbleServer(object):
    def __init__(
            self, server_url, session_key, api_key, debug=False,
            username=False):
        self.server_url = server_url
        self.session_key = session_key
        self.api_key = api_key
        self.debug = debug

        self.log = None
        self.post_data = []
        if debug:
            self.log = open(username + '.response.log', 'w+')

    def submit(self):
        if len(self.post_data) == 0:
            return

        i = 0
        data = []
        last_error = None

        for listen in self.post_data:
            data += listen.get_tuples(i)
            i += 1

        data += [
            ('method', 'track.scrobble'),
            ('sk', self.session_key),
            ('api_key', self.api_key),
            ('format', 'json'),
        ]

        for timeout in (1, 2, 4, 8, 16, 32):
            try:
                req = Request(self.server_url, urlencode(data))
                response = urlopen(req)
            except (URLError, HTTPError) as e:
                last_error = str(e)
                print('Scrobbling error, will retry in {}s:\n{}'.format(
                    timeout, last_error))
            else:
                json_response = json.load(response)

                # Checking if key exists
                if 'scrobbles' in json_response:
                    if self.debug:
                        for v in json_response['scrobbles']['scrobble']:
                            self.log.write(str(v) + '\n')
                    break
                elif 'error' in json_response:
                    last_error = 'Bad server response: {}'.format(
                        json_response['error'])
                    print('Scrobbling error, will retry in {}s:\n{}'.format(
                        timeout, last_error))
                else:
                    last_error = 'Bad server response: {}'.format(
                        response.read())
                    print('Scrobbling error, will retry in {}s:\n{}'.format(
                        last_error, timeout))
            time.sleep(timeout)
        else:
            raise ScrobbleException(
                'Cannot scrobble after multiple retries. \n'
                + 'Last error: {}'.format(last_error))

        self.post_data = []
        time.sleep(1)

    def add_listen(self, listen):
        i = len(self.post_data)
        if i > 49:
            self.submit(time.sleep(1))
            i = 0
        self.post_data.append(listen)


class ScrobbleTrack(object):

    def __init__(self, timestamp, title, artist, album=None,
                 title_mbid=None, track_length=None, track_number=None):
        self.timestamp = timestamp
        self.title = title
        self.artist = artist
        self.album = album
        self.title_mbid = title_mbid
        self.track_length = track_length
        self.track_number = track_number

    def get_tuples(self, i):
        data = []
        data += [
            ('timestamp[%d]' % i, self.timestamp),
            ('track[%d]' % i, self.trackname),
            ('artist[%d]' % i, self.artistname)
        ]

        if self.album is not None:
            data.append(('album[%d]' % i, self.album))
        if self.title_mbid is not None:
            data.append(('mbid[%d]' % i, self.title_mbid))
        if self.track_length is not None:
            data.append(('duration[%d]' % i, self.track_length))
        if self.track_number is not None:
            data.append(('tracknumber[%d]' % i, self.track_number))

        return data
