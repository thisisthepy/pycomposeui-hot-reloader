import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import threading

from pycomposeui_hot_reloader.src.main.server.observer import start_monitoring


async def send_file_change_info(current_event, ws_connections: dict):
    """This Function makes the server send the change information to clients

    :return: None
    """
    tasks = []

    for ws in ws_connections.keys():
        if not ws_connections[ws]:
            tasks.append(asyncio.create_task(send_file_and_close(ws=ws, current_event=current_event)))
            ws_connections[ws] = True
    await asyncio.gather(*tasks)


async def send_file_and_close(ws: WebSocket, current_event):
    #print(f'Now Trying to send the information to the websocket: ({ws})')
    await ws.send_text(str(current_event))
    print(f'The event {current_event} was sent to the client (ws:{ws}).')
    await ws.close()

async def on_startup(directory_to_watch: str, os_list: list, zipfile_dir: str,
                     ws_connections: dict):
    """This Function goes up when the server has been called."""
    #event_finished = asyncio.Event() # Event to synchronize tasks
    current_event = await start_monitoring(os_list=os_list, directory_to_watch=directory_to_watch,
                                           zipfile_dir=zipfile_dir)
    #print(f'---***The current event is {current_event}***---')
    await send_file_change_info(current_event=current_event, ws_connections=ws_connections)

def start_reloading(directory_to_watch: str = None, zipfile_dir: str = None, os_list: list = None,
                    ws_connections: dict = {}, current_event: dict = None):
    """This function is used to run the server and main processes.
        Args:
            directory_to_watch: This determines the directory to be watched.
            zipfile_dir: This determines the directory to save the zipped files.
            os_list: (Optional) This saves the list of OS.
            ws_connections: This saves the list of the sockets which are currently connected.
            current_event: This saves the current file changes as a dictionary.

    """
    app = FastAPI()
    zipfile_dir = zipfile_dir
    os_list = os_list


    async def on_connect(ws: WebSocket):
        """This function runs when the Websocket is connected."""
        await ws.accept()
        if ws not in ws_connections.keys():
            ws_connections[ws] = False
            print(f'The current ws_connections is {ws_connections}.')

    async def on_disconnect(ws: WebSocket, close_code: int):
        """This function runs when the Websocket is disconnected."""

        print(f'The current ws_connections is {ws_connections}.')
        if ws in ws_connections.keys():
            try:
                await ws.close()
            except WebSocketDisconnect as e:
                print(f"WebSocket({ws}) already closed with close_code({close_code}).")
                print(f"The event code is {e.code}: {e.reason}")

            finally:
                del ws_connections[ws]

    app.add_event_handler("startup",
                          lambda: asyncio.create_task(on_startup(directory_to_watch=directory_to_watch,
                                                                 os_list=os_list, zipfile_dir=zipfile_dir,
                                                                 ws_connections=ws_connections)))


    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        """ Set up a WebSocket endpoint and establish a connection on the client side.
        This Function Does Three processes When the WebSocket was called.
                1. Await the change of files
                2. send the changed Information to the client
                3. close the websocket."""
        await on_connect(ws)
        try:

            try:  # avoiding the case to try closing the webSocket after it was already closed
                while True:
                    data = await ws.receive_text()
                    if data == "close":
                        break
            except WebSocketDisconnect as e:
                print(f"WebSocketDisconnect Error occured with code {e.code}: {e.reason}")
                pass
            finally:
                await on_disconnect(ws, 1000)
        except Exception as e:
            print(f"Exception occurred: {e}")
            await on_disconnect(ws, 1001)

    @app.get("/client/{os_name}.zip")
    async def os_zip(os_name: str):
        """Enable Windows client to download the newest zip file."""
        print(f'INFO: The following application has been updated now: {os_name}')
        if os_name in os_list:
            if "\\" in zipfile_dir:
                return FileResponse(path=f"{zipfile_dir}\\zip_files\\{os_name}.zip", filename=f"{os_name}.zip")
            else:
                return FileResponse(path=f"{zipfile_dir}/zip_files/{os_name}.zip", filename=f"{os_name}.zip")
        else:
            raise HTTPException(status_code=404, detail='The OS is not found.')  # TODO: Add 404 error


    @app.get("/")
    @app.get("/index.html")
    async def index():
        """Show the change logs on the Web."""
        index_template = ""
        with open(os.path.dirname(sys.argv[0]) + "/res/static/templates/index.template", "r", encoding="UTF-8") as index:
            index_template = index.readlines()
        if str(type(index_template)) == "<class 'list'>":
            index_template = "\n".join(index_template)
        return HTMLResponse(index_template)

    return app

# the place for make_zip function


