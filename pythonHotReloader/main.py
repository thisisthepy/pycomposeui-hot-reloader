from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

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
import asyncio
import threading
import os
import zipfile


app = FastAPI()

# This object will store filesystem change events.
CURRENT_EVENT = None
# Flag to indicate whether the information has been sent.
INFORMATION_SENT = False
#Path to be watched, the default path is current directory.
DIRECTORY_TO_WATCH = os.getcwd() + "\\app\\src"
#Make list of OS Directories.
OS_LIST = []
#the list of directories which are not tracked.
EXCEPTION_LIST = ["common", "__pycache__", "zipFiles"]

for item in os.listdir(DIRECTORY_TO_WATCH):
    sub_folder = os.path.join(DIRECTORY_TO_WATCH, item)
    print(f'Checking current directories.... : {sub_folder}')
    if os.path.isdir(sub_folder): # Check if sub_folder is a directory.
        if item not in EXCEPTION_LIST:
            OS_LIST.append(item)

class CustomHandler(FileSystemEventHandler):
    '''Except Opened or Closed events, This class make the object to track the Events using watchdog.FileSystemEventHandler.
    '''
    def compress_zip(self, target_OS: str, TARGET_DIR: str = DIRECTORY_TO_WATCH, DESTINATION_DIR: str = os.getcwd() + "\\zipFiles"):
        '''Make a zipfile which is composed with files in 'common' and target directory.
        '''
        if not os.path.exists(DESTINATION_DIR):
            #if there is no directory in the path, exspecially while initializing, make the directory which will store the zipFiles
            os.mkdir(DESTINATION_DIR)

        FILE_NAME = f'{DESTINATION_DIR}\\{target_OS}.zip'
        zipped_dir = zipfile.ZipFile(FILE_NAME, 'w')

        for (path, dir, files) in os.walk(TARGET_DIR):
            print(f'the current path is {path}')    
            if target_OS in path or 'common' in path:
                os.chdir(TARGET_DIR)
                print(f'the current dir is {dir}')
                print(f'the current files is {files}')
                for file in files:
                    print(file)
                    zipped_dir.write(os.path.join(os.path.relpath(path, TARGET_DIR), file), compress_type=zipfile.ZIP_DEFLATED)
        zipped_dir.close()

    def on_any_event(self, event):
        '''If there is a new event in watched directory, this function saves the event in the list objective named "CURRENT_EVENT".
        '''
        global CURRENT_EVENT, INFORMATION_SENT, OS_LIST
        
        if event.event_type != 'opened' and event.event_type != 'closed':
            if not event.is_directory: 
                #Take actions for tracking changes of a file.
                crnt_path = DIRECTORY_TO_WATCH + "\\"
                event_dir = event.src_path.replace(crnt_path, '')
                if "\\" in event_dir:
                    #exract the OS tag of file
                    #Save the directory's name, not file, as the event_dir.
                    event_dir = event_dir.split('\\')[0]
                else:
                    event_dir = 'src'
                if event_dir != 'zipFiles':
                    CURRENT_EVENT = [event.src_path, event_dir, event.event_type, event.is_directory]
                
                if event_dir == 'common':
                    for OS in OS_LIST:
                        self.compress_zip(target_OS = OS)
                
                elif event_dir in OS_LIST:
                    print(f'event_dir is {event_dir}')
                    self.compress_zip(target_OS = event_dir)
                
                elif event_dir != 'zipFiles':
                    print(f'[Unnamed OS Error] The directory that has not been saved as OS was found, named as {event_dir}.')
                    print(f'The Tracked file is {event.src_path}.')
                    print(f'The event type is {event.event_type}.')

                INFORMATION_SENT = False  # Reset the flag when a new event occurs.
            
            else:
                #If you want to make new OS, Take actions about this procedure.
                #The below code is just for an example.

                print(f'A New Directory has been founded, whose path is {event.src_path}.')

def start_monitoring(directory_to_watch, event_finished):
    '''Using CusomHandler Class, This function starts to track the directory.
    '''
    event_handler = CustomHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    #'Schedule' method came from class, BaseObserver in observers.api
    observer.start()
    event_finished.set()  # Signal that the event handling is finished.

@app.on_event("startup")
def startup_event():
    '''This Function goes up when the server has been called.'''
    global DIRECTORY_TO_WATCH # Use a path that you initially defined.

    event_finished = threading.Event()  # Event to synchronize threads
    thread = threading.Thread(target=start_monitoring, args=(DIRECTORY_TO_WATCH, event_finished))
    #This procedure runs the function named start_monitoring in a sub-thread.
    thread.start()
    event_finished.wait() # Wait for the event handling to finish before starting the next thread.

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    '''Setting up a WebSocket endpoint and establish a connection on the client side.
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
</body>
</html>
    """)