"""
        This Python3 script communicates via websockets to a Node-Red interface, to try to recognise images using Tensorflow trained InceptionV3 model.
        This script is tested and runs on a single or cluster of Raspberry Pi 3 model B's, companied with Tensorflow v1.8.0 and Node-Red v0.18.4.
        
        This project was made for our second year of bachelor education in Electronics - IT, Security, Systems & Services at Thomas More - campus De Nayer.

        GitHub repo: https://github.com/ri4dh/ImageRecognition_RPiCluster
        Authors: Riadh Ben Hassine r0658451 r0658451@student.thomasmore.be / riadhbenhassine@protonmail.com
                 Yannick Buelens   r0657624 r0657624@student.thomasmore.be / yannick.buelens1@gmail.com
"""

#import necessary modules
import time
import websocket
import threading
from tornado import websocket as ws_server
import tornado.ioloop
import asyncio
import json
import tensorflow as tf
import sys
import urllib.request

#function to send data to the listening websocket of the Node-Red interface
def sendMessage(bericht):
        ws = websocket.WebSocket();#declare new websocket
        ws.connect("ws://localhost:1880/nodeWSserver")#connect to websocket address defined in Node-Red
        ws.send(bericht)#send message
        ws.close()#close connection
        
#function to be called to compare an image with the trained model
def checkImage(afbeelding):
            #make empty array to append scores later
            scores = []
            #declare some image vars
            image_path = afbeelding
            image_data = tf.gfile.FastGFile(image_path, 'rb').read()
            #load trained labels
            label_lines = [line.rstrip() for line 
                               in tf.gfile.GFile("./retrained_labels.txt")]
            #load trained model and use it
            with tf.gfile.FastGFile("./retrained_graph.pb", 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                _ = tf.import_graph_def(graph_def, name='')
            #run the Tensorflow session
            with tf.Session() as sess:
                softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
                predictions = sess.run(softmax_tensor, \
                         {'DecodeJpeg/contents:0': image_data})
                top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
                #for every known category, append score + prediction percentage to array
                for node_id in top_k:
                    human_string = label_lines[node_id]
                    score = predictions[0][node_id]
                    #for debug purposes, print every prediction to console
                    print('%s (score = %.5f)' % (human_string, score))
                    #append score
                    scores.append((human_string, score))
                return scores

#class that's listening on port 9000, this class gets data from the Node-Red interface and calls checkImage function to compare downloaded image with the model.
class EchoWebSocket(ws_server.WebSocketHandler):
    #for debug purposes, print whenever websocket connection is initiated    
    def open(self):
        print("Websocket Opened")
    #whenever the websocket receives a message, do the following    
    def on_message(self, message):
        #prepare empty message to reply
        messageToSend = ""
        #convert json message to readable dictionary
        info = json.loads(message)
        #for debug purposes, print URL from image
        print(info["Foto"])
        #download the image using the "urllib" module, and save it as 'test.jpg'
        urllib.request.urlretrieve(info["Foto"], 'test.jpg')
        #for debug purposes, print when the application starts comparing image to model
        print("start check")
        #try and catch for error handling of unkown image formats
        try:
                #call checkImage function and write the result into score
                score = checkImage('test.jpg')
                #for debug purposes, print the highest score (first item in array)
                print(score[0])
                #append key(categorie) and value(percentage) from the score var to new vars
                key, value = score[0]
                #form message to send to the Node-Red interface, the message is in the format of a sentence to use the tts module in Node-Red
                messageToSend = "I am ready. I am key:" + str(round((value*100),2)) + "% sure that it is a " + key + " ."
                #send message to Node-Red
                sendMessage(messageToSend)
                #form new message to send percentage separately (gauge)
                messageToSend = "percent:"+str(round((value*100),2))
                #send message
                sendMessage(messageToSend)
        except:
                #if an error occurs, send errormessage to interface to let the user know something went wrong
                sendMessage("Oops, There went something wrong.<br/>Please choose a different image.")
    #for debug purposes, when websocket connection gets closed, print to console
    def on_close(self):
        print("Websocket closed")
#define tornado web application to run the class EchoWebSocket
application = tornado.web.Application([(r"/", EchoWebSocket),])
#make the application listen on port 9000
application.listen(9000)
#start the tornado instance in a loop
tornado.ioloop.IOLoop.instance().start()
