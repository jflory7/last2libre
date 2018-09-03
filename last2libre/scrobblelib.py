import json
import logging
import time

from urllib.parse import urlencode
from urllib.request import Request, URLError, HTTPError, urlopen

logger = logging.getLogger(__name__)


class InvalidScrobbleServer(Exception):
    pass


class ScrobbleException(Exception):
    pass


class ScrobbleServer(object):
    def __init__(
            self, server_url, session_key, api_key, username=False):
        self.server_url = server_url
        self.session_key = session_key
        self.api_key = api_key
        self.debug = debug

        self.post_data = list()

    def submit(self):
        if len(self.post_data) == 0:
            logger.error('No data to submit. Canceling.')
            return

        i = 0
        data = list()
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
        logger.debug('data: {}'.format(data))

        for timeout in (1, 2, 4, 8, 16, 32):
            try:
                req = Request(self.server_url, urlencode(data))
                response = urlopen(req)
            except (URLError, HTTPError) as e:
                last_error = str(e)
                logger.error('Scrobbling error, will retry in {}s: {}'.format(
                    timeout, last_error))
            else:
                json_response = json.loads(response)

                # Checking if key exists
                if 'scrobbles' in json_response:
                    for v in json_response['scrobbles']['scrobble']:
                        logger.debug(str(v))
                    break
                elif 'error' in json_response:
                    last_error = 'Bad server response: {}'.format(
                        json_response['error'])
                    logger.error('Scrobbling error, will retry in '
                        + '{}s: {}'.format(imeout, last_error))
                else:
                    last_error = 'Bad server response: {}'.format(
                        response.read())
                    logger.error('Scrobbling error, will retry in '
                        + '{}s: {}'.format(last_error, timeout))
            time.sleep(timeout)
        else:
            raise ScrobbleException(
                'Cannot scrobble after multiple retries. \n'
                + 'Last error: {}'.format(last_error)
            )

        self.post_data = list()
        time.sleep(1)

    def add_listen(self, listen):
        i = len(self.post_data)
        if i > 49:
            self.submit()
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
        data = list()
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
