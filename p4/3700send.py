#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

DATA_SIZE = 1375

class Sender:
    def __init__(self, host, port):
        self.host = host
        self.remote_port = int(port)
        self.log("Sender starting up using port %s" % self.remote_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.waiting = False
        
        self.sws = 3
        self.lar = 0
        self.lfs = 0
        self.acks = 0
        self.seqnum = 0
        self.frames_sent = []

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def send(self, message):
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
                    msg_d = json.loads(msg)
                    temp_seq = msg_d['seqnum']
                    
                    if temp_seq != self.lar:
                        self.lar = temp_seq
                    
                    
                    self.acks += 1
                    print('waiting?',self.lar,self.lfs, self.acks)
                    if self.acks == self.sws:
                        self.waiting = False
                        self.acks = 0
                        print('made it')
                        print(self.frames_sent)
                    
                elif conn == sys.stdin:
                    data = sys.stdin.read(DATA_SIZE)
                    if len(data) == 0:
                        self.log("All done!")
                        self.send({"type": "FIN"})
                        sys.exit(0)
                        
                    
                    self.seqnum += 1
                    
                    msg = { "type": "msg", "data": data, "seqnum": self.seqnum }
                    self.log("Sending message '%s'" % msg)
                    self.send(msg)
                    self.frames_sent.append((self.seqnum))
                    self.lfs = self.seqnum
                    
                    if self.seqnum - self.lar == self.sws:
                        self.waiting = True

        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()