import socket
import sys

LOCAL_HOST = "172.16.22.24"
#udpserver.py
##################################################################
#                  Formatted Print statements                    #
##################################################################
# We provided some print statements to assist with
# formatting the outputs for the autograder  :)

# To print to indicate when the server starts:
## print(f"Server started on port {port}. Accepting connections",flush=True)


# To print the received message after receiving the expression 
# from the client use:
## print(f"Received operation: {op1} {op2} {op}",flush=True)
# OR
## print(f"Received operation: {expression_x}",flush=True)

# Note: Replace variables inside {} with your own variables

# REMINDER: Use sys.stdout.flush() after or flush=True inside 
# any print statements to ensure that the output is printed
# on the terminal before timeout.

def start_udp_server(inputArgv):
    
    if len(inputArgv) != 2:
        print('Invalid Command Line Arguements', len(inputArgv), flush= True) ###
        return
    
    port = int(inputArgv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
        # Bind the socket to the port
        server_address = (LOCAL_HOST, port)
        server_socket.bind(server_address)
        print(f"Server started on port {port}. Accepting connections", flush= True) 
        return server_socket, port
    except Exception as e:
        print(e, flush= True) ###
    
def operate_server(server_socket):
    while True:
        # Receive response
        data, addr = server_socket.recvfrom(1024)
        # To print the received message after receiving the expression 
        # from the client use:
        data = data.decode().split(' ')
        #print(data, addr) ###
        op1 = data[0]
        op2 = data[1]
        op = data[2]
        print(f"Received operation: {op1} {op2} {op}",flush=True)
        
        # Send data
        server_socket.sendto(f"recieved".encode(), addr)
        


if __name__ == "__main__":
    server_socket, port = start_udp_server(sys.argv)
    try:
        operate_server(server_socket)
    except KeyboardInterrupt:
        server_socket.close()