#!/usr/bin/env python

import argparse
import logging
import os

from last2libre import importer, exporter, __version__

logging.basicConfig(
    datefmt='%Y-%m-%dT%H:%M:%S',
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=os.environ.get("LOGLEVEL", "INFO"),
)
logger = logging.getLogger(__name__)


def sub_export(args):
    transaction = exporter.Exporter(
        api_key=args.key,
        entity_type=args.entity_type,
        out_file=args.out,
        page_number=args.page,
        server=args.server,
        user=args.username,
    )
    transaction.run()
    logger.debug('Export transaction completed.')


def sub_import(args):
    try:
        transaction = importer.Importer(
            in_file=args.input,
            api_key=args.key,
            server=args.server,
            server_url=args.server_url,
            entity_type=args.entity_type,
            username=args.username,
        )
        transaction.run()
    except InvalidScrobbleServer as iss:
        logger.critical(iss)
        raise SystemExit(0)
    logger.debug('Import transaction completed.')


def main():
    # Create main parser and subparser
    parser = argparse.ArgumentParser(
        description='Download and export Last.fm scrobbles and loved tracks.',
    )
    subparsers = parser.add_subparsers()

    # Create global parser flags
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__,
    )

    # Create parser for 'export' subcommand
    parser_export = subparsers.add_parser(
        'export',
        aliases=['e'],
        help='export from platform',
    )
    parser_export.add_argument(
        '-k', '--key',
        default=None,
        help='API key to use for music service platform',
        metavar='API_KEY',
        type=str,
    )
    parser_export.add_argument(
        '-o', '--out',
        default='lastfm_raw_export.txt',
        help='Path to saved data file',
        metavar='FILE',
        type=str,
    )
    parser_export.add_argument(
        '-p', '--page',
        default=1,
        help='Page number to start fetching tracks from [default: 1]',
        metavar='PAGE_NUMBER',
        type=int,
    )
    parser_export.add_argument(
        '-s', '--server',
        choices=['custom', 'lastfm', 'librefm'],
        default='lastfm',
        help='Server to export listen history from [default: lastfm]',
        type=str,
    )
    parser_export.add_argument(
        '-t', '--type',
        choices=['scrobbles', 'loved', 'banned'],
        default='scrobbles',
        dest='entity_type',
        help='Type of information to export [default: scrobbles]',
        type=str,
    )
    parser_export.add_argument(
        '-u', '--user',
        default=None,
        dest='username',
        help='Your username on service',
        metavar='USERNAME',
        required=True,
        type=str,
    )
    parser_export.set_defaults(func=sub_export)

    # Create parser for 'import' subcommand
    parser_import = subparsers.add_parser(
        'import',
        aliases=['i'],
        help='import to platform',
    )
    parser_import.add_argument(
        '-d', '--debug',
        action='store_true',
        default=False,
        dest='debug',
        help='Verbose debug logging',
    )
    parser_import.add_argument(
        '-i', '--input',
        default=None,
        help='Path to saved data file',
        metavar='FILE',
        required=True,
        type=str,
    )
    parser_import.add_argument(
        '-k', '--key',
        default=None,
        help='API key to use for music service platform',
        metavar='API_KEY',
        type=str,
    )
    parser_import.add_argument(
        '-s', '--server',
        choices=['custom', 'librefm'],
        default='librefm',
        help='Server to import listen history into [default: librefm]',
        type=str,
    )
    parser_import.add_argument(
        '--server-url',
        default=None,
        help='Base URL of custom GNU.fm server',
        type=str,
    )
    parser_import.add_argument(
        '-t', '--type',
        choices=['scrobbles', 'loved', 'banned', 'unloved', 'unbanned'],
        default=None,
        dest='entity_type',
        help='Type of information to import',
        required=True,
        type=str,
    )
    parser_import.add_argument(
        '-u', '--user',
        default=None,
        dest='username',
        help='Your username on service',
        metavar='USERNAME',
        required=True,
        type=str,
    )
    parser_import.set_defaults(func=sub_import)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
