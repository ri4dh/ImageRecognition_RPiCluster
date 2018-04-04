import time
import websocket
import threading
from tornado import websocket as ws_server
import tornado.ioloop
import asyncio
import json
import tensorflow as tf
import sys

def sendMessage(bericht):
        ws = websocket.WebSocket();
        ws.connect("ws://localhost:1880/test")
        ws.send(bericht)
        ws.close()
def checkImage(afbeelding):
            scores = {}
            image_path = afbeelding
            image_data = tf.gfile.FastGFile(image_path, 'rb').read()
            label_lines = [line.rstrip() for line 
                               in tf.gfile.GFile("./retrained_labels.txt")]
            with tf.gfile.FastGFile("./retrained_graph.pb", 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                _ = tf.import_graph_def(graph_def, name='')
            with tf.Session() as sess:
                softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
                predictions = sess.run(softmax_tensor, \
                         {'DecodeJpeg/contents:0': image_data})
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[0][node_id]
                    print('%s (score = %.5f)' % (human_string, score))
                    scores[human_string]=score
                return scores

class EchoWebSocket(ws_server.WebSocketHandler):
    def open(self):
        print("Websocket Opened")

    def on_message(self, message):
        messageToSend = ""
        info = json.loads(message)
        print(info["Foto"])
        score = checkImage(info["Foto"])
        print(list(score.items())[0])
        key, value = list(score.items())[0]
        messageToSend = "Ik ben klaar, Ik ben key:" + str(round((value*100),2)) + "% zeker dat het een " + key + " is."
        sendMessage(messageToSend)
        messageToSend = "percent:"+str(round((value*100),2))
        sendMessage(messageToSend)

    def on_close(self):
        print("Websocket closed")

application = tornado.web.Application([(r"/", EchoWebSocket),])
application.listen(9000)
tornado.ioloop.IOLoop.instance().start()
