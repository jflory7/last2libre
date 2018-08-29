#!/usr/bin/env python

import argparse

import exporter


def sub_export(args):
    transaction = exporter.Exporter(
        api_key=args.key,
        entity_type=args.entity_type,
        out_file=args.out,
        page_number=args.page,
        server=args.server,
        user=args.username,
    )
    transaction.export()


def sub_import(args):
    pass


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
        version='%(prog)s :-(',
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
        help='Server to fetch track info from [default: lastfm]',
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
        '-i', '--in',
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
        required=True,
        type=str,
    )
    parser_import.add_argument(
        '-s', '--server',
        default='last.fm',
        help='Server to fetch track info from [default: last.fm]',
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
