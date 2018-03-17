CS 3251 Programming Assignment 2
3/16/2018
Elizbeth McConnell elizabeth.mcconnell@gatech.edu
Nick Giammanco ngiammanco@gatech.edu

Files Submitted:
 - ringo.py : implementation of project
 - README.txt : file detailing our implementation


To run program:
User input cannot be inputted until Peer Discovery is complete. Please wait ~5 seconds to ensure it is all sent correctly. 

python ringo.py <flag> <local-port> <POC-name> <POC-Port> <N>

- <flag>: type of Ringo
    S: Sender
    R: Receiver
    F: Forwarder
- <local-port>: the UDP port number the Ringo will use 
- <POC-name>: host name of POC. 0 if the ringo has no POC
- <POC-port>: the UDP port number of the POC for this ringo. 0 if ringo has no POC
- <N>: total number of ringos when theyre all active

Working Commands:
    show-matrix: shows RTT matrix
    show-ring: shows path for optimal ring
