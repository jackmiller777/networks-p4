#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

DATA_SIZE = 1375

# Get the block number from a message, return False on failure
def Get_Block_ID(msg):
    data = msg['data']
    if data[0:12] == '----- Block ':
        return data[12:19]
    else:
        return False;
    
class SendQueue:
    queue = {}
    
    # Append packet by id, overriding if there is anything with the given id
    def append(self, msg):
        block_id = Get_Block_ID(msg)
        self.queue[block_id] = msg
        
    # Get a packet based on the id number, if not found return false
    def get_packet(self, block_id):
        try:
            return[block_id]
        except:
            return False

class Sender:
    def __init__(self, host, port):
        self.host = host
        self.remote_port = int(port)
        self.log("Sender starting up using port %s" % self.remote_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.waiting = False
        self.window_sz = 2
        self.sent = 0
        self.recved = 0
        self.send_q = SendQueue()
        self.ack_ids = []
        self.first_conn = True
        self.num_packets = 0
        self.packet_index = 0
        self.data = []

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def send(self, message):
        #message["window_sz"] = self.window_sz
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.host, self.remote_port))

    def run(self):
        while True:
            sockets = [self.socket, sys.stdin] if not self.waiting else [self.socket]

            socks = select.select(sockets, [], [], 0.1)[0]
            for conn in socks:
                if conn == self.socket:
                    k, addr = conn.recvfrom(65535)
                    msg = k.decode('utf-8')

                    self.log("Received message '%s'" % msg)
                    self.recved += 1
                    msg_dict = json.loads(msg)
                    ack_id = msg_dict['ack_id'] 
                    self.window_sz = msg_dict['window_sz']
                    
                    if ack_id in self.ack_ids:
                        self.log("Received duplicate ack")
                        self.waiting = True
                    else:
                        if self.recved < self.sent:
                            self.waiting = True
                        else:
                            self.sent = 0
                            self.recved = 0
                            self.waiting = False
                            
                    self.ack_ids.append(ack_id)
                    
                    print(len(self.ack_ids), self.num_packets)
                    if len(self.ack_ids) == self.num_packets:
                        self.log("All done!")
                        sys.exit(0)
                    
                elif conn == sys.stdin:
                    if self.first_conn:
                        self.num_packets = self.get_data()
                        self.first_conn = False
                        print('num_packets', self.num_packets)

                    
                    print('packet_index', self.packet_index)
                    print('xxx', self.num_packets - self.packet_index)
                    msg = { "type": "msg", "data": self.data[self.packet_index], "window_sz": self.window_sz }
                    self.packet_index += 1
                    self.log("Sending message '%s'" % msg)
                    self.send(msg)
                    self.sent += 1
                    
                    if self.sent == self.window_sz or self.sent == self.num_packets:
                        self.waiting = True
                        self.window_sz = min(self.window_sz, self.num_packets - self.packet_index)

        return
    
    def get_data(self):
        num_packets = 0
        while (True):
            read = sys.stdin.read(DATA_SIZE)
            self.data.append(read)
            if len(read) == 0:
                break;
            
            num_packets += 1
            
        return num_packets

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()
