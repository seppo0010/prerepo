import os
import time

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.utils.dirsnapshot import DirectorySnapshot

from prerepo.client.models import File


class PrerepoEventHandler(LoggingEventHandler):
    def __init__(self, f=None, path=None):
        super(PrerepoEventHandler, self).__init__()
        self.f = f
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
        self.f = File(uid=uid, server=server)

    def watch(self):
        def create(path, stat_info):
            remote_path = path[len(self.path) - 1:]
            if os.path.isdir(path):
                self.f.createdir(remote_path)
            else:
                with open(path, 'r') as fp:
                    self.f.createfile(remote_path, fp.read())

        event_handler = PrerepoEventHandler(f=self.f, path=self.path)
        observer = Observer()
        observer.schedule(event_handler, path=self.path, recursive=True)
        observer.start()
        DirectorySnapshot(self.path, recursive=True, walker_callback=create)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
