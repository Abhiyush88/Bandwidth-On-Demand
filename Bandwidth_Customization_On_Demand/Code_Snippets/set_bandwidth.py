from flask import Flask, render_template, redirect, url_for, request
import threading
import socket
import json
import logging
import collections
import re
from read_file import *

logging.basicConfig(level=logging.DEBUG)

OVSDB_IP = '127.0.0.1'
OVSDB_PORT = 6632
sock = '/var/run/openvswitch/db.sock'

# create the application object
app = Flask(__name__)

def default_echo_handler(message, ovsconn):
    logging.debug("responding to echo")
    ovsconn.send({"result": message.get("params", None),
                  "error": None, "id": message['id']})

def default_message_handler(message, ovsconn):
    logging.debug("default handler called for method %s", message['method'])
    ovsconn.responses.append(message)

# use decorators to link the function to a url
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('home.html')  # return a string

def get_port_details(ovsdb):
    switch_host = {}
    host_mac = request.form['Host_Mac']
    switch_host = sw_host.get(host_mac)[-1]
    print "Switch_Host: %s" %(sw_host)
    get_port_query = {"method": "transact", "params": ['Open_vSwitch',
    {
        "op": "select",
        "table": "Port",
        "where": [["name", "==", switch_host]],
        "columns": ["_uuid"]
    }],"id": 0}

    ovsdb.send(json.dumps(get_port_query))
    p_uuid = ovsdb.recv(4096)
    print p_uuid
    pt_uuid = re.sub(r'[^-\w]', ' ', p_uuid).split()
    print "port_uuid: %s" %(pt_uuid[6])
    return pt_uuid[6]

def insert_to_queue(ovsdb):
    min_bw = request.form['MinBandwidth']
    max_bw = request.form['MaxBandwidth']

    insert_queue_query = {"method": "transact", "params": ['Open_vSwitch',
    {
        "op": "insert",
        "table": "Queue",
        "row":  {
            "other_config": [
                    "map",
                    [
                        [
                            "max-rate",
                             max_bw
                        ],
                        [
                            "min-rate",
                             min_bw
                        ],
                    ]
                ]
                }}],"id": 1}

    ovsdb.send(json.dumps(insert_queue_query))
    q_uuid = ovsdb.recv(4096)
    queue_uuid = re.sub(r'[^-\w]', ' ', q_uuid).split()
    logging.debug("queue_uuid: %s", queue_uuid[5])
    return queue_uuid[5]


def insert_to_qos(ovsdb, queue_uuid):
    
    insert_qos_query = {"method": "transact", "params": ['Open_vSwitch',
    {
        "op": "insert",
        "table": "QoS",
        "row":  {
            "type": "linux-htb",
            "queues": [
                    "map",
                    [
                      [
                        0,
                        [
                            "uuid",
                             queue_uuid
                        ],
                      ]
                    ]
                ]
                }}],"id": 2}

    ovsdb.send(json.dumps(insert_qos_query))
    uuid = ovsdb.recv(4096)
    qos_uuid = re.sub(r'[^-\w]', ' ', uuid).split()
    logging.debug("qos_uuid: %s", qos_uuid[5])
    return qos_uuid[5]


def update_port(ovsdb, qos_uuid, port_uuid):

    update_port_query = {"method": "transact", "params": ['Open_vSwitch',
    {
        "op": "update",
        "table": "Port",
        "where": [["_uuid", "==", ["uuid", port_uuid]]],
        "row": {"qos": ["set", [["uuid", qos_uuid]]]}
    }],"id": 3}
    
    print "Port_uuid: %s" %(port_uuid)
    ovsdb.send(json.dumps(update_port_query))
    p_count = ovsdb.recv(4096)
    count = re.sub(r'[^-\w]', ' ', p_count).split()
    logging.debug("%s record inserted successfully", count[4])
 

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ovsdb = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ovsdb.connect(sock)
        logging.debug("Connection to ovsdb successful")
        port_uuid = get_port_details(ovsdb)
        queue_uuid = insert_to_queue(ovsdb)
        logging.debug("Successfully inserted new record into Queue table UUID of the new record is : %s", queue_uuid)
        qos_uuid = insert_to_qos(ovsdb, queue_uuid)
        logging.debug("Successfully inserted new record into QoS table UUID of the new record is : %s", qos_uuid)
        update_port(ovsdb, qos_uuid, port_uuid)
        ovsdb.close()
        logging.debug("Connection to ovsdb closed successfully.")
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(host='192.168.0.22', debug=True)


