from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import shutil
import os
import zipfile
import asyncio
import threading
import uvicorn

from watchdog.observers import Observer
'''In main.py, this module will use WindowsApiObserver 
'''
from watchdog.events import FileSystemEventHandler
'''FileSystemEventHandler
    : notified for 
            EVENT_TYPE_CREATED: self.on_created,
            EVENT_TYPE_DELETED: self.on_deleted,
            EVENT_TYPE_MODIFIED: self.on_modified,
            EVENT_TYPE_MOVED: self.on_moved,
            EVENT_TYPE_CLOSED: self.on_closed,
            EVENT_TYPE_OPENED: self.on_opened,
'''

app = FastAPI()

# Global variables to store filesystem change events and upload status.
CURRENT_EVENT = None
INFORMATION_SENT = False

# Path to be watched, the default path is current directory.
DIRECTORY_TO_WATCH = os.getcwd() + "\\app\\src"
ZIPFILES_DIR = os.getcwd() + "\\zipFiles"

# Make a list of OS Directories and a list of directories which are not tracked.
OS_LIST = []
EXCEPTION_LIST = ["common", "__pycache__", "zipFiles"]

# Populate the OS_LIST with directories that are not in the EXCEPTION_LIST.
for item in os.listdir(DIRECTORY_TO_WATCH):
    sub_folder = os.path.join(DIRECTORY_TO_WATCH, item)
    print(f'Checking current directories.... : {sub_folder}')
    if os.path.isdir(sub_folder) and item not in EXCEPTION_LIST:
        OS_LIST.append(item)

class CustomHandler(FileSystemEventHandler):
    '''Class to handle filesystem change events'''
    def compress_zip(self, target_OS: str, TARGET_DIR: str = DIRECTORY_TO_WATCH, DESTINATION_DIR: str = os.getcwd() + "\\zipFiles"):
        '''Make a zipfile which is composed with files in 'common' and target directory.'''
        if not os.path.exists(DESTINATION_DIR):
            # if there is no directory in the path, exspecially while initializing, make the directory which will store the zipFiles
            os.mkdir(DESTINATION_DIR)

        FILE_NAME = f'{DESTINATION_DIR}\\{target_OS}.zip'
        zipped_dir = zipfile.ZipFile(FILE_NAME, 'w')

        for (path, _, files) in os.walk(TARGET_DIR):
            if target_OS in path or 'common' in path:
                os.chdir(TARGET_DIR)
                for file in files:
                    zipped_dir.write(os.path.join(os.path.relpath(path, TARGET_DIR), file), compress_type=zipfile.ZIP_DEFLATED)
        zipped_dir.close()

    def on_any_event(self, event):
        '''Handles any filesystem event Except Opening and Closing'''
        global CURRENT_EVENT, INFORMATION_SENT, OS_LIST
        
        if event.event_type != 'opened' and event.event_type != 'closed':
            if not event.is_directory: 
                # Take actions for tracking changes of a file.
                crnt_path = DIRECTORY_TO_WATCH + "\\"
                event_dir = event.src_path.replace(crnt_path, '')
                if "\\" in event_dir:
                    # exract the OS tag of file
                    # Save the directory's name, not file, as the event_dir.
                    event_dir = event_dir.split('\\')[0]
                else:
                    event_dir = 'src'

                if event_dir != 'zipFiles':
                    CURRENT_EVENT = [event.src_path, event_dir, event.event_type, event.is_directory]
                
                if event_dir == 'common':
                    for OS in OS_LIST:
                        self.compress_zip(target_OS = OS)
                
                elif event_dir in OS_LIST:
                    self.compress_zip(target_OS = event_dir)
                
                elif event_dir != 'zipFiles':
                    print(f'[Unnamed OS Error] The directory that has not been saved as OS was found, named as {event_dir}.')
                    print(f'The Tracked file is {event.src_path}.')
                    print(f'The event type is {event.event_type}.')

                INFORMATION_SENT = False  # Reset the flag when a new event occurs.
            
            else:
                # If you want to make new OS, Take actions about this procedure.
                # The below code is just for an example.

                print(f'A New Directory has been founded, whose path is {event.src_path}.')

def start_monitoring(directory_to_watch, event_finished):
    '''Starts tracking the directory'''
    event_handler = CustomHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    # 'Schedule' method came from class, BaseObserver in observers.api
    observer.start()
    event_finished.set()  # Signal that the event handling is finished.

@app.on_event("startup")
def startup_event():
    '''This Function goes up when the server has been called.'''
    global DIRECTORY_TO_WATCH # Use a path that you initially defined.

    event_finished = threading.Event()  # Event to synchronize threads
    thread = threading.Thread(target=start_monitoring, args=(DIRECTORY_TO_WATCH, event_finished))
    # This procedure runs the function named start_monitoring in a sub-thread.
    thread.start()
    event_finished.wait() # Wait for the event handling to finish before starting the next thread.

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    '''Set up a WebSocket endpoint and establish a connection on the client side.
    This Function Does Three processes When the WebSocket was called.
            1. Await the change of files
            2. send the changed Information to the client 
            3. close the websocket.'''
    global INFORMATION_SENT
    try:
        await ws.accept()
        while True:
            if not INFORMATION_SENT and CURRENT_EVENT:
                await ws.send_text(str(CURRENT_EVENT))
                INFORMATION_SENT = True
                await ws.close()  # Close the WebSocket connection after sending the information.
            await asyncio.sleep(1)
    except WebSocketDisconnect as e:
        print(f"WebSocket closed with code {e.code}: {e.reason}")
    
@app.get("/IOS.zip")
async def zip():
    '''Enable IOS client to download the newest zip file.'''
    return FileResponse(path= f"{ZIPFILES_DIR}/IOS.zip", filename="IOS.zip")
       
@app.get("/Windows.zip")
async def zip():
    '''Enable Windows client to download the newest zip file.'''
    return FileResponse(path= f"{ZIPFILES_DIR}/Windows.zip", filename="Windows.zip")
       

@app.get("/Android.zip")
async def zip():
    '''Enable Android client to download the newest zip file.'''
    return FileResponse(path= f"{ZIPFILES_DIR}/Android.zip", filename="Android.zip")
    

@app.get("/")
async def root():
    '''Show the change logs on the Web.
    '''
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

# Run uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)