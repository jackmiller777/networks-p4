#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

# Get the block number from a message, return False on failure
def Get_Block_ID(msg):
    data = msg['data']
    if data[0:12] == '----- Block ':
        return data[12:19]
    else:
        return False;

class Receiver:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.port = self.socket.getsockname()[1]
        self.log("Bound to port %d" % self.port)

        self.remote_host = None
        self.remote_port = None
        
        
        self.rws = 3
        self.laf = self.rws
        self.lfr = 0
        
        self.seqnum = 0
        self.frames = 0
        
        self.buffer = {}
        self.seqnums = []
        self.blocknums = []
        self.acks_sent = []
        
        self.done = False
        
        self.t_lr = time.time()
        self.t_curr = time.time()

    def send(self, message):
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.remote_host, self.remote_port))

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def timeout(self):
        self.t_curr = time.time()
        if self.t_curr - self.t_lr > 1000:
            return True
        else:
            return False
        
    def run(self):
        while True:
            socks = select.select([self.socket], [], [])[0]
            for conn in socks:
                data, addr = conn.recvfrom(65535)
                print(self.t_lr)
                # Grab the remote host/port if we don't already have it
                if self.remote_host is None:
                    self.remote_host = addr[0]
                    self.remote_port = addr[1]

                msg = json.loads(data.decode('utf-8'))
                self.log("Received data message %s" % msg)
                self.t_lr = time.time()
                
                if msg['type'] == 'FIN':
                    self.done = True
                elif msg['seqnum'] not in self.seqnums and msg['seqnum'] != self.lfr:
                    self.seqnum = msg['seqnum']
                    self.lfr = msg['seqnum']
                    blocknum = Get_Block_ID(msg)
                    self.buffer[blocknum] = msg
                    self.seqnums.append(self.seqnum)
                    self.blocknums.append(blocknum)
                
                    self.frames += 1
                    
                    laflfr = str(self.laf) + ', ' + str(self.lfr) + ', ' + str(self.frames)
                    self.log(laflfr)
                    
                self.log(str(str(msg['seqnum']) + ', ' + str(msg['seqnum'] not in self.seqnums)))
                
                if self.frames == self.rws or self.timeout() or self.done:
                    for blocknum in sorted(self.blocknums):
                        self.log('sort ' + str(blocknum))
                        msg = self.buffer[blocknum]
                        # Print out the data to stdout
                        print(msg["data"], end='', flush=True)
                        # Always send back an ack
                        self.send({ "type": "ack", "seqnum": msg['seqnum'] })
                        self.acks_sent.append(msg['seqnum'])

                    self.laf = self.laf + self.rws
                        
                    self.buffer = {}
                    self.blocknums = []
                    self.seqnums = []
                    self.frames = 0
                    self.log(str('ACKS: ' + str(self.acks_sent)))
                

        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()