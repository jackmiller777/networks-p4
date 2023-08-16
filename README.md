miller.john 
README.md
3700 Proj 4

Packet Forwarding Client/Server Simulation

High-level approach:
I approached this project by going level by level, as explained below.

Level 1: I started with a fixed window of 2, although I had a lot of trouble understanding the concept. I spent a lot of time at this point understanding the starter code, simulation, and static window protocol.

Level 2: To pass the level two tests, I simply added sequence numbers to each packet, and used a list to keep track of received sequence numbers. If a packet shows up with a repeated sequence number, it is dropped.

Level 3: At this level, I added buffers to the sender and receiver that store packets by sequence number, and are deleted when the window is complete. Because I implemented a static window of 4 here, I got very stuck, and ran out of time to implement a sliding window. Instead, my code goes window by window, adjusting the window size based on gathered information about the network.

Level 4: I added ack checking at the sender to ensure that all packets sent are acked. If acks arrive out of order or not at all, frames are resent.

Level 5: For detecting packet corruption, I added a hash checksum to packets and compared them at the receiver, as well as checking that all packets are in json format. Corrupted packets are dropped.

Level 6: I added latency checking at each of my windows and set the rtt once each window was complete.

Level 7: My design did not have window sliding because I ran out of time. Instead, my code goes window by window, growing the window by 2 or shrinking it by 1. 

Testing:
I tested my code with the given simulator, as well as logging values at important points.