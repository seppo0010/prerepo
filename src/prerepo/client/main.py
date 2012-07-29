from argparse import ArgumentParser
import os
import sys

from watcher import Watcher


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--directory', dest='directory', required=True,
            help='Path of  the directory to watch')
    parser.add_argument('-u', '--uid', dest='uid', required=True,
            help='Unique identifier for your project.')
    parser.add_argument('-s', '--server', dest='server',
            default='http://127.0.0.1:5000/',
            help='Base URL for your project server.')
    args = parser.parse_args()

    # allow absolute or relative paths
    path = os.path.join(os.getcwd(), args.directory)
    if not os.access(path, os.X_OK):
        sys.stderr.write('Unable to open directory for execution')
        sys.exit(1)

    Watcher(path=path, uid=args.uid, server=args.server).watch()


if __name__ == '__main__':
    main()
