import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

from prerepo.client.models import File


class PrerepoEventHandler(LoggingEventHandler):
    def __init__(self, uid=None, server=None, path=None):
        super(PrerepoEventHandler, self).__init__()
        self.f = File(uid=uid, server=server)
        self.path = path

    def get_remote_path(self, path):
        return path[len(self.path) - 1:]

    def on_created(self, event):
        path = event.src_path
        if event.is_directory:
            self.f.createdir(self.get_remote_path(path))
        else:
            with open(path, 'r') as fp:
                self.f.createfile(self.get_remote_path(path), fp.read())

    def on_moved(self, event):
        self.f.rename(self.get_remote_path(event.src_path),
            self.get_remote_path(event.dest_path))
        # TODO: rename files on move directories

    def on_deleted(self, event):
        self.f.delete(self.get_remote_path(event.src_path))

    def on_modified(self, event):
        path = event.src_path
        if not event.is_directory:
            with open(path, 'r') as fp:
                self.f.createfile(self.get_remote_path(path), fp.read())


class Watcher(object):
    def __init__(self, path=None, uid=None, server=None):
        super(Watcher, self).__init__()
        self.path = path
        self.uid = uid
        self.server = server

    def watch(self):
        event_handler = PrerepoEventHandler(uid=self.uid, server=self.server,
                path=self.path)
        observer = Observer()
        observer.schedule(event_handler, path=self.path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
