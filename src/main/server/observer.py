import os
import sys
import zipfile
import asyncio
import traceback
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class ConnectionManager:
    def __init__(self):
        self.client_connections = {}
        self.lock = asyncio.Lock()

    async def add_os(self, os_name: str):
        async with self.lock:
            self.client_connections[os_name] = []

    async def add_queue(self, os_name: str, queue: asyncio.Queue):
        async with self.lock:
            if os_name not in self.client_connections:
                self.client_connections[os_name] = []
            self.client_connections[os_name].append(queue)

    async def delete_os(self, os_name: str):
        async with self.lock:
            del self.client_connections[os_name]

    async def delete_queue(self, os_name: str, queue: asyncio.Queue):
        async with self.lock:
            self.client_connections[os_name].remove(queue)
            if len(self.client_connections[os_name]) == 0:
                del self.client_connections[os_name]

    async def get_client_connections(self):
        async with self.lock:
            return self.client_connections


class FileModificationEventPublisher(PatternMatchingEventHandler):
    """Class to detect filesystem change events and Create its message to channel"""
    def __init__(self,
                 os_list: list, directories_to_watch: list, zipfile_dir: str,
                 event_channel, loop,
                 patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=True):

        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.os_list = os_list
        self.directories_to_watch = directories_to_watch
        self.zipfile_dir = zipfile_dir
        self.event_channel = event_channel
        self.current_event = asyncio.Future()
        self.loop = loop

    def on_any_event(self, event):
        if self.ignore_patterns:
            if not any(event.src_path.startswith(ignore) for ignore in self.ignore_patterns):
                asyncio.run_coroutine_threadsafe(self.handle_event(event), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.handle_event(event), self.loop)

    async def handle_event(self, event):
        """Handles any filesystem event Except Opening and Closing"""
        if event.event_type != 'opened' and event.event_type != 'closed':
            if '~' not in event.src_path:
                # Take actions for tracking changes of a file.
                sys.stdout.write(f'Changed file information: {event.src_path}\n')

                target_dir = ''
                for _dir in self.directories_to_watch:
                    if _dir in event.src_path:
                        target_dir = event.src_path.replace(_dir, '')[1:]

                event_dir = 'common'

                for os_name in self.os_list:
                    if os_name in target_dir:
                        event_dir = os_name

                sys.stdout.write(f'The OS which has been modified : [{event_dir}].\n')
                self.current_event.set_result({'src_path': event.src_path,
                                               'os_tag': event_dir,
                                               'event_type': event.event_type,
                                               'dir_flag': event.is_directory})

                self.current_event = asyncio.Future()  # Reset current_event to track future events

                if event_dir in self.os_list:
                    self.event_channel.trigger_event(event_dir,
                                                     target_os=event_dir,
                                                     directory_to_watch=target_dir,
                                                     zipfile_dir=self.zipfile_dir)
                elif event_dir == 'common':
                    for os in self.os_list:
                        self.event_channel.trigger_event(os,
                                                         target_os=os,
                                                         directory_to_watch=target_dir,
                                                         zipfile_dir=self.zipfile_dir)

                else:
                    sys.stderr.write(f'[Unknown OS Error] The directory that has not been saved as OS was found: '
                                     f'{event_dir}.\n')
                    sys.stdout.write(f'The Tracked file is {event.src_path}.\n')
                    sys.stdout.write(f'The event type is {event.event_type}.\n')
                    return traceback.format_exc()


class FileModificationEventChannel:
    def __init__(self):
        self.event_handlers = {}
        self.current_event = None

    def add_event_handler(self, event_name, event_handler):
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(event_handler)

    def trigger_event(self, event_name, *args, **kwargs):
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                handler(*args, **kwargs)
        else:
            sys.stdout.write(f'The event ({event_name}) is not on the list of event handlers.\n')
            sys.stdout.write(f'Please check the process to create list. The current list is '
                             f'{self.event_handlers.keys()}.\n')
            return traceback.format_exc()


def make_zip(target_os: str, directory_to_watch: str, zipfile_dir: str):
    """Make a zipfile which is composed with files in 'common' and target directory."""

    zipfile_dir = os.path.join(zipfile_dir, 'zip_files')
    file_name = os.path.join(zipfile_dir, f'{target_os}.zip')

    if not os.path.exists(zipfile_dir):
        # if there is no directory in the path, especially initializing, make the directory to store the zipFiles
        os.mkdir(zipfile_dir)

    zipped_dir = zipfile.ZipFile(file_name, 'w')

    for (path, _, files) in os.walk(directory_to_watch):
        if target_os in path or 'commonMain' in path:
            os.chdir(directory_to_watch)
            for file in files:
                if "~" in path:
                    pass
                else:
                    zipped_dir.write(os.path.join(
                        os.path.relpath(path, directory_to_watch), file),
                        compress_type=zipfile.ZIP_DEFLATED)
    zipped_dir.close()
    sys.stdout.write(f'INFO:  Packaging the zipped files for {target_os} has just been completed!\n')


async def start_monitoring(os_list: list, directories_to_watch: list, exception_dir: list, zipfile_dir: str):
    """Starts tracking the directories
        Args:
            os_list (list): This saves the list of OS.
            directories_to_watch (list): This determines the directories to be watched.
            exception_dir (list): This determines the directories not to be watched.
            zipfile_dir (str): This determines the directory to save the zipped files.
        Return:
            current_event (dict) : This saves the information about file change.
    """

    event_channel = FileModificationEventChannel()

    for os_name in os_list:
        event_channel.add_event_handler(os_name, make_zip)

    loop = asyncio.get_running_loop()

    # Create the event handler with the callback function.
    event_handler = FileModificationEventPublisher(os_list=os_list, directories_to_watch=directories_to_watch,
                                                   zipfile_dir=zipfile_dir, event_channel=event_channel,
                                                   loop=loop, ignore_patterns=exception_dir)

    observer = Observer()
    for _dir in directories_to_watch:
        observer.schedule(event_handler, _dir, recursive=True)
    observer.start()

    return await event_handler.current_event
