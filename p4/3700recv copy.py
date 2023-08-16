#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

# Get the block number from a message, return False on failure
def Get_Block_ID(msg):
    data = msg['data']
    if data[0:12] == '----- Block ':
        return data[12:19]
    else:
        return False;

class RecvQueue:
    queue = {}
    
    def __len__(self):
        return len(self.queue)
    
    # Append packet by id, overriding if there is anything with the given id
    def append(self, msg):
        block_id = Get_Block_ID(msg)
        self.queue[block_id] = msg
        
    # Get a packet based on the id number, if not found return false
    def get(self, block_id):
        try:
            return self.queue[block_id]
        except KeyError:
            return False
        
    # return dict item function
    def items(self):
        return self.queue.items()
        
    
class Receiver:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.port = self.socket.getsockname()[1]
        self.log("Bound to port %d" % self.port)

        self.remote_host = None
        self.remote_port = None
        
        self.msgs = []
        self.window_sz = 4
        self.recved = 0
        self.recv_q = RecvQueue()
        self.block_ids = []
        self.ack_id = 0

    def send(self, message):
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.remote_host, self.remote_port))

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def run(self):
        while True:
            socks = select.select([self.socket], [], [])[0]
            for conn in socks:
                data, addr = conn.recvfrom(65535)

                # Grab the remote host/port if we don't alreadt have it
                if self.remote_host is None:
                    self.remote_host = addr[0]
                    self.remote_port = addr[1]

                msg = json.loads(data.decode('utf-8'))
                
                block_id = Get_Block_ID(msg)
                self.log(str(self.recv_q.get(block_id)))
                if not self.recv_q.get(block_id):
                    self.recv_q.append(msg)
                    self.block_ids.append(block_id)
                    sent_window_sz = msg['window_sz']
                    self.recved += 1
                else:
                    self.log('Received Duplicate Packet with ID %s' % block_id)
                
                self.log('sz: %i ' % len(self.recv_q))
                nums = str(self.recved) + ', ' + str(self.window_sz)
                self.log(nums)
                if self.recved == sent_window_sz:
                    for block_id in sorted(self.block_ids):
                        msg = self.recv_q.get(block_id)
                        self.log("Received data message %s" % msg)
                        # Print out the data to stdout
                        print(msg["data"], end='', flush=True)
                        
                        # Always send back an ack
                        self.send({ "type": "ack", "block_id": block_id, "ack_id": self.ack_id, "window_sz": self.window_sz })
                        self.ack_id += 1
                    self.recved = 0
                    self.block_ids = []
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()
