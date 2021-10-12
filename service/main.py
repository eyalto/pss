import os
import pika
import logging
import munch
import json
from api import init_api
from flask import Flask, request, jsonify
from flask_healthz import healthz, HealthError
import threading
from threading import Thread
from cli.CliWrapper import Cli
from prometheus_client import start_http_server, Summary, Counter

default_config = {
    "api": {
        "port": 8001
    },
    "monitor": {
        "port": 5080
    },
    "log" : {
        "name": "pacs_store_service",
        "level": "DEBUG"
    },
    "pacs": {
        "host": "127.0.0.1",
        "port": 8080,
        "aet" : "AEZEBRA",
        "aec": "PACS"
    },
    "rabbit": {
        "host": "localhost",
        "port": 5672,
        "queue": "pacsStoreDicomsQueue"
    }
}

_alive = False
_ready = False
HEALTHZ = {
    "live": "main.liveness",
    "ready": "main.readiness",
}


# initialize conf
conf_filename = os.environ.get('PSSCONFIG') if 'PSSCONFIG' in os.environ else "config.json"
config = json.load(open(conf_filename)) if os.path.isfile(conf_filename) else default_config
conf = munch.munchify(config)
# initialize log
level = logging.DEBUG if conf.log.level == "DEBUG" else logging.INFO
logging.basicConfig(level=level, format='%(levelname)s: %(name)s: %(asctime)s %(message)s')
logger = logging.getLogger(conf.log.name)
# initialize monitor
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
c_success = Counter('sent_success_counter', 'Success sending counter')
c_failurs = Counter('sent_failurs_counter', 'Failur sending counter')
c_msgcount = Counter('message_counter', 'Service overall requests counter')

# global api server
app = Flask(__name__)
app.register_blueprint(healthz,"/healthz")
app.config['HEALTHZ']=HEALTHZ

def liveness():
    logger.info("liveness check")
    pass

def readiness():
    logger.info("readiness check")
    pass

@REQUEST_TIME.time()
def handle_message(ch, method, properties, msgbody):
    """
    handle a rabbit message with files to send though the queue
    """
    c_msgcount.inc()
    msg = munch.munchify(json.loads(msgbody))
    # msg override configuration options of pacs details 
    pacs_host = msg.host if 'host' in msg.keys() and msg.host else conf.pacs.host
    pacs_port = msg.port if 'port' in msg.keys() and msg.port else conf.pacs.port
    pacs_aetitle = msg.aet if 'aet' in msg.keys() and msg.aet else conf.pacs.aet
    my_aetitle = msg.aec if 'aec' in msg.keys() and msg.aec else conf.pacs.aec
    # try sending
    for dicom_path in msg.filesReferences.files:
        try:
            store_path_to_pacs(pacs_host,pacs_port,pacs_aetitle, my_aetitle, dicom_path.path)
            logger.info(f"successfully stored :{dicom_path.path}")
        except ConnectionError as e:
            logger.info(f"unable to store dicom {dicom_path.path}")
            logger.warn(f"{str(e)}: error connecting to pacs host:{pacs_host} port {pacs_port}")
            c_failurs.inc()
        else:
            c_success.inc()


def store_path_to_pacs(pacs_host, pacs_port, pacs_aetitle, my_aetitle, dicom_path ):
    '''
        store all the dicom files in the path filtered by .dcm file ext
    '''
    if not os.path.exists(dicom_path):
        raise(FileNotFoundError(dicom_path))
    
    cli = Cli("storescu", logger)
    rc, error = cli.run(command_line_args=['-aet', pacs_aetitle, '-aec', my_aetitle, '-v', '--recurse',
                                   '--scan-directories', pacs_host, str(pacs_port), dicom_path] )
    if rc != 0:
        logger.error(f"rc: {rc} error pushing path {dicom_path} with message {error}")
        raise(ConnectionError(f"pacs rc:{rc} host:{pacs_host} port:{pacs_port}  msg:{error}"))

def rabbitmq_setup():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=conf.rabbit.host, port=conf.rabbit.port))
    channel = connection.channel()
    channel.queue_declare(queue=conf.rabbit.queue)
    return channel

def rabbitmq_start(channel):
    channel.basic_consume(queue=conf.rabbit.queue, on_message_callback=handle_message, auto_ack=True)
    logging.info("starting to consume messages ... ")
    channel.start_consuming()

def start_monitor_server():
    start_http_server(conf.monitor.port)

def start_rabbitmq_consumer_thread(channel):
    t = Thread(target=rabbitmq_start,args=(channel,))
    t.start()    
    return t

def get_liveliness():
    return _liveliness
    
def excepthook(args):
    global _liveliness
    _liveliness = False
    logging.info(f"Unhandled exception: type {str(args.exc_type)} thread {str(args.thread)}")

def main():
    logger.info(f"main starting with following configuration: {json.dumps(conf,indent=2)}")
    threading.excepthook = excepthook
    # monitor
    try:
       start_monitor_server()
    except Exception as e: 
        logger.warn(f"error initializing prometheus metric serving client: exception msg {str(e)} - exiting.")
        exit(1)
    # messaging consumer
    try:
        channel = rabbitmq_setup()
        t = start_rabbitmq_consumer_thread(channel)
    except Exception as e:
        logger.error(f"failed starting rabbitmq consumer - error {str(e)} - exiting.")
        exit(1)
    # service api handler
    try:
        api=init_api(conf)
        api.init_app(app)
        app.run(port=conf.api.port)
    except Exception as e:
        logger.error(f"failed initilaizing api server - error {str(e)} - exiting.")

if __name__ == "__main__":
    # run everything
    main()