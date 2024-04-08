from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import zipfile
import asyncio
import threading
import uvicorn

# Global variables to store filesystem change events and upload status.
CURRENT_EVENT = None
INFORMATION_SENT = False
ws_connections = set()


async def send_file_change_info():
    """This Function makes the server send the change information to clients
    
    :return: None
    """
    global CURRENT_EVENT, INFORMATION_SENT, ws_connections
    while True:
        if CURRENT_EVENT and not INFORMATION_SENT:
            message = str(CURRENT_EVENT)
            for ws in ws_connections.copy():  # Iterate over a copy to avoid modification during iteration
                try:
                    await ws.send_text(message)
                    print(f'The event {CURRENT_EVENT} was sent to the client (ws:{ws}).')
                    INFORMATION_SENT = True
                    await ws.close()
                except WebSocketDisconnect:
                    print(f'WebSocket {ws} disconnected while sending message.')
                    if ws in ws_connections:
                        ws_connections.remove(ws)  # Remove disconnected WebSocket
        await asyncio.sleep(1)


def start_monitoring(directory_to_watch, event_finished, os_list, zipfile_dir):
    """Starts tracking the directory"""
    event_handler = CustomHandler(os_list, directory_to_watch, zipfile_dir)
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    # 'Schedule' method came from class, BaseObserver in observers.api
    observer.start()
    event_finished.set()  # Signal that the event handling is finished.


def on_startup(directory_to_watch: str,
               os_list: list, zipfile_dir: str):
    """This Function goes up when the server has been called."""

    event_finished = threading.Event()  # Event to synchronize threads
    thread = threading.Thread(target=start_monitoring,
                              args=(directory_to_watch, event_finished, os_list, zipfile_dir))
    # This procedure runs the function named start_monitoring in a sub-thread.
    thread.start()
    event_finished.wait()  # Wait for the event handling to finish before starting the next thread.
    asyncio.create_task(send_file_change_info())


def start_reloading(DIRECTORY_TO_WATCH: str = None, ZIPFILE_DIR: str = None,
                    OS_LIST: list = None):
    """This function is used to run the server and main processes.
        Args:
            DIRECTORY_TO_WATCH: This determines the directory to be watched.
            ZIPFILE_DIR: This determines the directory to save the zipped files.
            OS_LIST : (Optional) This saves the list of OS.
        Global variable = CURRENT_EVENT: (Don't initialize) This saves the current event that was tracked lately.
    """
    global CURRENT_EVENT
    app = FastAPI()

    async def on_connect(ws: WebSocket):
        """This function runs when the Websocket is connected."""
        global ws_connections
        await ws.accept()
        if ws not in ws_connections:
            ws_connections.add(ws)
            print(f'The current ws_connections is {ws_connections}.')

    async def on_disconnect(ws: WebSocket, close_code: int):
        """This function runs when the Websocket is disconnected."""
        global ws_connections
        ws_connections.remove(ws)
        print(f'The current ws_connections is {ws_connections}.')
        if ws in ws_connections:
            try:
                await ws.close()
            except WebSocketDisconnect as e:
                print(f"WebSocket({ws}) already closed with close_code({close_code}).")
                print(f"The event code is {e.code}: {e.reason}")

    app.add_event_handler("startup",
                          lambda: on_startup(directory_to_watch=DIRECTORY_TO_WATCH,
                                             os_list=OS_LIST, zipfile_dir=ZIPFILE_DIR))

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        """ Set up a WebSocket endpoint and establish a connection on the client side.
        This Function Does Three processes When the WebSocket was called.
                1. Await the change of files
                2. send the changed Information to the client
                3. close the websocket."""
        global INFORMATION_SENT, CURRENT_EVENT
        await on_connect(ws)
        try:
            while True:
                if not INFORMATION_SENT and CURRENT_EVENT:
                    try:  # avoiding the case to try closing the webSocket after it was already closed
                        data = await ws.receive_text()
                        if data == "close":
                            break
                    except WebSocketDisconnect as e:
                        await on_disconnect(ws, e.code)
                        print(f"WebSocket({ws}) closed with code {e.code}: {e.reason}")
                        break
        except Exception as e:
            print(f"Exception occurred: {e}")
            await on_disconnect(ws, 1001)

    @app.get(f"/{os_name}.zip")
    async def os_zip(zipfile_dir=ZIPFILE_DIR):
        """Enable Windows client to download the newest zip file."""
    for os_name in OS_LIST:
        return FileResponse(path=f"{zipfile_dir}/{os_name}.zip", filename=f"{os_name}.zip")


    @app.get("/")
    async def root():
        """Show the change logs on the Web.
        """
        return HTMLResponse("""
        <!DOCTYPE html>
    <html>
    <head>
        <title>File Watcher</title>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var eventsList = document.getElementById("eventsList");
                var newEvent = document.createElement("li");
                console.log(event.data);
                newEvent.textContent = event.data;
                eventsList.appendChild(newEvent);
                
            };
        </script>
    </head>
    <body>
        <h1>File Watcher</h1>
        <ul id="eventsList"></ul>
        <h2>Download Zip Files:</h2>
        <ul>
            <li><a href="/IOS.zip">Download IOS.zip</a></li>
            <li><a href="/Windows.zip">Download Windows.zip</a></li>
            <li><a href="/Android.zip">Download Android.zip</a></li>
        </ul>
    </body>
    </html>
        """)

    return app

# the place for make_zip function


class CustomHandler(FileSystemEventHandler):
    """Class to handle filesystem change events."""
    def __init__(self,
                 os_list, directory_to_watch, zipfile_dir):
        super().__init__()
        self.os_list = os_list
        self.directory_to_watch = directory_to_watch
        self.zipfile_dir = zipfile_dir

    def on_new_os(self, event):
        """This method is for the situation when entered a new OS which is not in OS_LIST"""
        # The below code is just for an example.
        print(f'A New Directory has been founded, whose path is {event.src_path}.')

    def make_zip(self,
                 target_os: str, directory_to_watch: str,
                 zipfile_dir: str):
        """Make a zipfile which is composed with files in 'common' and target directory."""
        zipfile_dir += '\\zip_files'
        if not os.path.exists(zipfile_dir):
            # if there is no directory in the path, especially initializing, make the directory to store the zipFiles
            os.mkdir(zipfile_dir)

        FILE_NAME = f'{zipfile_dir}\\{target_os}.zip'
        zipped_dir = zipfile.ZipFile(FILE_NAME, 'w')

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

    def on_any_event(self, event):
        """Handles any filesystem event Except Opening and Closing"""
        global INFORMATION_SENT
        if event.event_type != 'opened' and event.event_type != 'closed':
            if not ('~' in event.src_path and event.event_type != 'deleted'):
                global CURRENT_EVENT
                # Take actions for tracking changes of a file.
                current_path = self.directory_to_watch + "\\"
                event_dir = event.src_path.replace(current_path, '')

                if "\\" in event_dir:
                    # extract the OS tag of file
                    # Save the directory's name, not file, as the event_dir.
                    event_dir = event_dir.split('\\')[0].replace('Main', '')
                else:
                    event_dir.replace('Main', '')

                if event_dir != 'zip_files':
                    CURRENT_EVENT = [event.src_path, event_dir, event.event_type, event.is_directory]

                if event_dir == 'common' or event_dir == 'commonMain':
                    for OS in self.os_list:
                        self.make_zip(target_os=OS,
                                      directory_to_watch=self.directory_to_watch, zipfile_dir=self.zipfile_dir)

                elif event_dir in self.os_list:
                    self.make_zip(target_os=event_dir,
                                  directory_to_watch=self.directory_to_watch, zipfile_dir=self.zipfile_dir)
                elif event.is_directory:
                    print(f'event_dir is {event_dir}, and event_type is {event.event_type}.')

                else:
                    print(f'[Unnamed OS Error] The directory that has not been saved as OS was found: {event_dir}.')
                    print(f'The Tracked file is {event.src_path}.')
                    print(f'The event type is {event.event_type}.')
                    # If you want to make new OS, Take actions about this procedure.
                    self.on_new_os(event=event)

                INFORMATION_SENT = False  # Reset the flag when a new event occurs.
