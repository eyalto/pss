import os
import pika
import logging
import munch
import json
from cli.CliWrapper import Cli

default_config = {
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
        "queue": "pacsStoreDicomsQueue"
    }
}

conf = munch.munchify(default_config)
logger = logging.getLogger()

def handle_message(ch, method, properties, msgbody):
    msg = munch.munchify(json.loads(msgbody))
    #
    # msg override configuration options of pacs details 
    pacs_host = msg.pacs.host if 'pacs' in msg.keys() else conf.pacs.host
    pacs_port = msg.pacs.port if 'pacs' in msg.keys() else conf.pacs.port
    pacs_aetitle = msg.pacs.aet if 'pacs' in msg.keys() else conf.pacs.aet
    my_aetitle = msg.pacs.aec if 'pacs' in msg.keys() else conf.pacs.aec

    for dicom_path in msg.filesReferences.files:
        logger.info(f"path to store is:{dicom_path.path}")
        store_path_to_pacs(pacs_host,pacs_port,pacs_aetitle, my_aetitle, dicom_path.path)



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

def main():
    global conf 
    global logger
    conf_filename = os.environ.get('PSSCONFIG') if 'PSSCONFIG' in os.environ else ".pss_conf"
    config = json.load(open(conf_filename)) if os.path.isfile(conf_filename) else default_config
    conf = munch.munchify(config)

    level = logging.DEBUG if conf.log.level == "DEBUG" else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(name)s: %(asctime)s %(message)s')
    logger = logging.getLogger(conf.log.name)

    connection = pika.BlockingConnection(pika.ConnectionParameters(conf.rabbit.host))
    channel = connection.channel()
    channel.queue_declare(queue=conf.rabbit.queue)

    channel.basic_consume(queue=conf.rabbit.queue, on_message_callback=handle_message, auto_ack=True)

    logging.info("starting to consume messages ... ")
    channel.start_consuming()

if __name__ == "__main__":
    main()