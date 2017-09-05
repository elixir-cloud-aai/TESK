from flask import Flask
from flask import request
from werkzeug.contrib.fixers import ProxyFix
import pika

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello world!"

@app.route('/v1/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        #queue(request.get_json())
        queue(request.data)
        return "Succesfully queued task"
    else:
        querytasks()
        return "Succesfully queried task"


app.wsgi_app = ProxyFix(app.wsgi_app)

def queue(request):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq-service'))
    channel = connection.channel()
    channel.basic_publish(exchange'',
            routing_key='job1',
            body=request)
    print("Sent json to queue: ", request)
    connection.close()

def querytasks():
    print("NOT IMPLEMENTED")

if __name__ == '__main__':
    #app.run
    app.run(port=8000)
