from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
import os
import zipfile
import asyncio
import threading
import uvicorn

from src.main.server.observer import Observer, FileModificationDetectHandler

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
    event_handler = FileModificationDetectHandler(os_list, directory_to_watch, zipfile_dir)
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    # 'Schedule' method came from class, BaseObserver in observers.api
    observer.start()
    event_finished.set()  # Signal that the event handling is finished.


def on_startup(directory_to_watch: str, os_list: list, zipfile_dir: str):
    """This Function goes up when the server has been called."""

    event_finished = threading.Event()  # Event to synchronize threads
    thread = threading.Thread(target=start_monitoring,
                              args=(directory_to_watch, event_finished, os_list, zipfile_dir))
    # This procedure runs the function named start_monitoring in a sub-thread.
    thread.start()
    event_finished.wait()  # Wait for the event handling to finish before starting the next thread.
    asyncio.create_task(send_file_change_info())


def start_reloading(DIRECTORY_TO_WATCH: str = None, ZIPFILE_DIR: str = None, OS_LIST: list = None):
    """This function is used to run the server and main processes.
        Args:
            DIRECTORY_TO_WATCH: This determines the directory to be watched.
            ZIPFILE_DIR: This determines the directory to save the zipped files.
            OS_LIST : (Optional) This saves the list of OS.
        Global variable = CURRENT_EVENT: (Don't initialize) This saves the current event that was tracked lately.
    """
    global CURRENT_EVENT
    app = FastAPI()
    zipfile_dir = ZIPFILE_DIR
    os_list = OS_LIST

    index_template = ""
    with open("./res/static/templates/index.template", "r", encoding="UTF-8") as index:
        index_template = index.readlines()

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
                                             os_list=os_list, zipfile_dir=zipfile_dir))

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

    @app.get("/<os_name: str>.zip")
    async def os_zip(os_name: str):
        """Enable Windows client to download the newest zip file."""
        if os_name in os_list:
            return FileResponse(path=f"{zipfile_dir}/{os_name}.zip", filename=f"{os_name}.zip")
        else:
            return HTTPResponse()  # TODO: Add 404 error

    @app.get("/")
    @app.get("/index.html")
    async def index():
        """Show the change logs on the Web."""
        return HTMLResponse(index_template)

    return app

# the place for make_zip function

