# 发布者
import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5555")

while True:
    news = "Breaking News! Time: {}".format(time.time())
    socket.send_string(news)
    time.sleep(1)

# 订阅者
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5555")
socket.setsockopt_string(zmq.SUBSCRIBE, "")

while True:
    news = socket.recv_string()
    print("Received News: {}".format(news))