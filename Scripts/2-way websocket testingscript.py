import time
import websocket
import threading
from tornado import websocket as ws_server
import tornado.ioloop
import asyncio
import json
def sendMessage(bericht):
        ws = websocket.WebSocket();
        ws.connect("ws://localhost:1880/test")
        ws.send(bericht)
        print("Percentage verzonden")
        ws.close()      

class EchoWebSocket(ws_server.WebSocketHandler):
    def open(self):
        print("Websocket Opened")

    def on_message(self, message):
        info = json.loads(message)
        print(info["Foto"])
        percent = input("Geef percentage: ")
        sendMessage(percent + "%")

    def on_close(self):
        print("Websocket closed")

application = tornado.web.Application([(r"/", EchoWebSocket),])
application.listen(9000)
tornado.ioloop.IOLoop.instance().start()
