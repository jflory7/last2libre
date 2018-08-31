'''Import listens to Libre.fm or a custom Gnu.fm server.'''
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import getpass
import hashlib
import json
import os

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from last2libre.scrobblelib import ScrobbleException, ScrobbleServer, \
    ScrobbleTrack

LIBREFM_BASE_URL = 'https://libre.fm/2.0/?'


class Importer(object):

    def __init__(
            self, in_file, api_key, server, server_url, entity_type, username):
        self.in_file = in_file
        self.api_key = api_key
        self.server = server
        self.server_url = server_url
        self.entity_type = entity_type
        self.username = username

    def auth(self, password):
        passwd_md5 = hashlib.md5(password).hexdigest()
        token = hashlib.md5(self.username + passwd_md5).hexdigest()
        get_data = dict(
            method='auth.getMobileSession',
            username=self.username,
            authToken=token,
            format='json',
            api_key=self.api_key
        )

        req = self.server_url + urlencode(get_data)
        response = urlopen(req)

        try:
            json_response = json.load(response)
            self.session_key = json_response['session']['key']
        except Exception:
            print(json_response)
            raise SystemExit(1)

    def check_server(self):
        if self.server == 'librefm':
            self.server_url = LIBREFM_BASE_URL
        elif self.server == 'custom':
            self.server_url = self.server_url + '/2.0/?'

    def submit(self, artist, title):
        if self.entity_type == 'loved':
            libre_method = 'track.love'
        elif self.entity_type == 'unloved':
            libre_method = 'track.unlove'
        elif self.entity_type == 'banned':
            libre_method = 'track.ban'
        elif self.entity_type == 'unbanned':
            libre_method = 'track.unban'
        else:
            raise ScrobbleException(
                'Invalid entity type for submission method')

        post_data = dict(
            method=libre_method,
            artist=artist,
            track=title,
            session_key=self.session_key,
            format='json',
            api_key=self.api_key,
        )

        req = Request(self.server_url, urlencode(post_data))
        response = urlopen(req)

        try:
            json_response = json.load(response)
            status = json_response['lfm']['status']

            if status == 'ok':
                return True
        except Exception:
            raise
            return False

    def run(self):
        self.check_server()
        password = (os.getenv('L2L_PASSWORD', getpass.getpass()))
        self.auth(password)

        if self.datatype == 'scrobbles':
            scrobbler = ScrobbleServer(
                server_name=self.server,
                session_key=self.session_key,
                api_key=self.api_key,
                debug=self.debug,
                username=self.username,
            )

            f = open(self.in_file, 'r')
            n = 0
            for line in f.readlines():
                n += 1
                timestamp, title, artist, album, title_mbid, artist_mbid, \
                    album_mbid = line.strip("\n").split("\t")
                # Submission protocol does not specify artist / album MBID, so
                # we do not send them.
                scrobbler.add_listen(
                    ScrobbleTrack(timestamp, title, artist, album, title_mbid))
                print(
                    'Loading line {}/{}: Importing scrobble: {} by {}.'.format(
                        n, enumerate(f), title, artist))
            f.close()
            scrobbler.submit()

        else:
            f = open(self.in_file, 'r')
            n = 0
            for line in f.readlines():
                n += 1
                timestamp, title, artist, album, title_mbid, artist_mbid, \
                    album_mbid = line.strip("\n").split("\t")
                try:
                    self.submit(artist, title)
                    print(
                        'Submitting line {}/{}:\n'.format(n, enumerate(f)) +
                        '\tEntity type: {}\n'.format(self.entity_type) +
                        '{} by {} on'.format(title, artist, album))
                except Exception as e:
                    print(
                        'Error on line {}/{} ({} by {}):\n{}'.format(
                            n, enumerate(f), title, artist, e))
