"""
Export listens through a platform's API.

This class downloads listens from a supported platform via the platform's
API. Then, the listens are cleaned and written out into a text file.
"""
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

import time
import xml.etree.ElementTree as ET

from urllib.parse import urlencode
from urllib.request import urlopen

# import __version__
__version__ = '1.0.0-dev'


class Exporter(object):

    def __init__(
            self, api_key, entity_type, out_file, page_number, server, user):
        """Initialize class from parser arguments.

        Args:
            api_key: String with API key for intended platform
            out_file: String with file path to write data out to
            page_number: Integer with page number to begin on
            server: String containing type of server to export from
            type: String containing data type of listens to collect
            user: String containing username to export listens from
        """
        self.api_key = api_key
        self.out_file = out_file
        self.page_number = page_number
        self.server = server
        self.user = user

        if entity_type == 'banned':
            self.entity_type = 'bannedtracks'
        elif entity_type == 'loved':
            self.entity_type = 'lovedtracks'
        elif entity_type == 'scrobbles':
            self.entity_type = 'recenttracks'
        else:
            self.entity_type = ''

    def connect_server(self):
        """Connect to server and return a XML page.

        Returns:
            ?
        """

        # Build an API URL for the platform to export data from
        if self.server == 'lastfm':
            base_url = 'https://ws.audioscrobbler.com/2.0/?'
            url_vars = dict(
                method='user.get%s' % self.entity_type,
                api_key=self.api_key,
                user=self.user,
                page=self.page_number,
                limit=50)
        elif self.server == 'librefm':
            base_url = 'https://libre.fm/2.0/?'
            url_vars = dict(
                method='user.get%s' % self.entity_type,
                api_key=('%(prog)s' % __version__).ljust(32, '-'),
                user=self.username,
                page=self.page_number,
                limit=200)
        # Assume custom Libre.fm server
        else:
            if self.server[:7] != 'http://':
                self.server = 'http://%s' % self.server
            base_url = self.server + '/2.0/?'
            url_vars = dict(
                method='user.get%s' % self.entity_type,
                api_key=('%(prog)s' % __version__).ljust(32, '-'),
                user=self.username,
                page=self.page_number,
                limit=200)
        url = base_url + urlencode(url_vars)

        # Attempt connection to API URL
        for interval in (1, 5, 10, 62):
            try:
                f = urlopen(url)
                break
            except Exception as e:
                last_exc = e
                print('Exception occurred, retrying in {}s: {}'.format(
                    interval, e))
                time.sleep(interval)
        else:
            print('Failed to open page: {}'.format(url_vars['page']))
            raise last_exc

        # Retrieve XML page to export
        response = f.read()
        f.close()
        return response

    def get_listen_list(self, response):
        """Read XML page and get a list of listens and their info."""
        xml_page = ET.fromstring(response)
        listen_list = xml_page.getiterator('track')
        return listen_list

    def get_page_info(self, response):
        """Check how many pages of listens user has."""
        xml_page = ET.fromstring(response)
        total_pages = xml_page.find(self.entity_type).attrib.get('totalPages')
        return int(total_pages)

    def parse_listen(self, listen):
        """Extract info from every listen entry and output to list.

        Args:
            listen: String containing data for a single listen string to parse

        Returns:
            Sorted string of listen metadata.
        """
        if listen.find('artist').getchildren():
            # Artist info nested in loved / banned tracks XML
            artist_name = listen.find('artist').find('name').text
            artist_mbid = listen.find('artist').find('mbid').text
        else:
            artist_name = listen.find('artist').text
            artist_mbid = listen.find('artist').get('mbid')

        if listen.find('album') is None:
            # no album info for loved / banned tracks
            album_name = ''
            album_mbid = ''
        else:
            album_name = listen.find('album').text
            album_mbid = listen.find('album').get('mbid')

        track_name = listen.find('name').text
        track_mbid = listen.find('mbid').text
        date = listen.find('date').get('uts')

        # Prepare final output from listen metadata
        output = [date, track_name, artist_name, album_name,
                  track_mbid, artist_mbid, album_mbid]

        # Filter incorrect data
        for i, v in enumerate(output):
            if v is None:
                output[i] = ''

        return output

    def write_listens(self, listens, fp):
        """Write listens to an open file.

        Args:
            listens: List of listens (payload data)
            fp: File pointer to open file object
        """
        for fields in listens:
            fp.write(('\t'.join(fields) + '\n'))

    def get_tracks(self):
        current_page = self.page_number
        response = self.connect_server()
        total_pages = self.get_page_info(response)

        if self.page_number > total_pages:
            raise ValueError(
                'First page ({}) is higher than total pages ({}).'.format(
                    self.page_number, total_pages))

        while current_page <= total_pages:
            # Skip connect if on first page, already have that one stored.
            if current_page > self.page_number:
                response = self.connect_server()

            listen_list = self.get_listen_list(response)
            listens = []

            for listen in listen_list:
                # do not export currently playing track
                if 'nowplaying' not in listen.attrib or \
                        not listen.attrib['nowplaying']:
                    listens.append(self.parse_listen(listen))

            yield current_page, total_pages, listens

            current_page += 1
            time.sleep(.5)

    def run(self):
        listen_dict = dict()
        current_page = self.page_number  # for case of exception
        total_pages = -1  # ditto
        n = 0

        try:
            for current_page, total_pages, listens in self.get_tracks():
                print('Got page {} of {}.'.format(current_page, total_pages))
                for listen in listens:
                    if self.entity_type == 'recenttracks':
                        listen_dict.setdefault(listen[0], listen)
                    else:
                        # Cannot use timestamp as key for loved/banned tracks
                        # as it is not unique – skip over this listen
                        n += 1
                        listen_dict.setdefault(n, listen)
        except ValueError as ve:
            exit(ve)
        except Exception:
            raise
        finally:
            with open(self.out_file, 'a') as fp:
                listens = sorted(listen_dict.values(), reverse=True)
                self.write_listens(listens, fp)
                print(
                    'Wrote page {}-{} of {} to file {}'.format(
                        self.page_number, current_page,
                        total_pages, self.out_file))
