import json
import os
import time
from flask_restx import Api, Resource
from flask_restx import reqparse
from pika.spec import Channel
from werkzeug.datastructures import FileStorage
import pika 

BACKOFF = 3
SLEEP_TIMEOUT = 2

api = Api()
parser = api.parser()
parser.add_argument('files', required=True, action='append')
parser.add_argument('host', required=False)
parser.add_argument('port', required=False, type=int)
parser.add_argument('aet', required=False)
parser.add_argument('aec', required=False)

# TODO: check initialized successfully 
@api.route("/alive")
def alive_prob():
    return "OK"
    
# TODO: check if channel is up and ready for communication
@api.route("/ready")
def ready_prob():
    return "OK"

@api.route("/pss")
@api.expect(parser)
class MsgApi(Resource):
    def _build_msg(self, args):
        msg = {
            "filesReferences": {
                "files": []
            }
        }
        files = args['files']
        if 'port' in args: msg['port']= args['port']
        if 'host' in args: msg['host']= args['host'] 
        if 'aet' in args: msg['aet']= args['aet'] 
        if 'aec' in args: msg['aec']= args['aec'] 
        
        for file in files:
            if os.path.exists(file):
                msg["filesReferences"]["files"].append({"path":file})
            else:
                raise FileNotFoundError(file)

        return msg

    def _send_msg(self):
        args = parser.parse_args()
        try:
            msg = self._build_msg(args)
            attempts = 0
            while attempts < BACKOFF:
                try:
                    channel.basic_publish(exchange='', routing_key=conf.rabbit.queue, body=json.dumps(msg))
                    break
                except (pika.exceptions.ChannelWrongStateError,
                        pika.exceptions.StreamLostError,
                        pika.exceptions.ChannelClosed):
                    time.sleep(SLEEP_TIMEOUT)
                    rabbitmq_setup()
                    attempts +=1
        # log attempts
        except FileNotFoundError as e:
            return {"error-message": "FileNotFoundError: {}".format(str(e))}, 404
        else:
            return {
                "status": "Success",
                "msg": msg
            },202

    def get(self):
        return self._send_msg()

    def post(self):
        return self._send_msg()


def rabbitmq_setup():
    global channel
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=conf.rabbit.host, port=conf.rabbit.port))
    channel = connection.channel()
    channel.queue_declare(queue=conf.rabbit.queue)
    return channel

def init_api(config):
    global channel
    global conf
    conf = config
    channel = rabbitmq_setup()
    return api 