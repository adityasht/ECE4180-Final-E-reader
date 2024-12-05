import socket
import sys
# udpclient.py
##################################################################
#                  Formatted Print statements                    #
##################################################################
# We provided some print statements to assist with
# formatting the outputs for the autograder  :)

# To print for invalid expression use:
## print("Invalid expression", flush=True)

# To print the final result for total value use:
## print(f"Total: {value}", flush=True)

# To print the sending message when sending to the server use:
## print(f"Sending operation: {op1} {op2} {op}", flush=True)
# OR 
## print(f"Sending operation: {expression_x}", flush=True)

# To print the error message after three timeouts use:
## print("Error - No response after 3 attempts", flush=True)

# Note: Replace variables inside {} with your own variables

# REMINDER: Use sys.stdout.flush() after or flush=True inside 
# any print statements to ensure that the output is printed
# on the terminal before timeout.

def start_udp_client(inputArgv):
    
    hostname = inputArgv[1]
    port = int(inputArgv[2])


    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        server_address = (socket.gethostbyname(hostname), port)

        client_socket.connect(server_address)
    
    except socket.gaierror:
        raise Exception(f"Failed to resolve hostname: {hostname}")
    except Exception as e:
        raise Exception(f"Failed to create UDP client: {str(e)}")
    
    client_socket.settimeout(2.0)
    return client_socket


def send_udp_message(client_socket, op1, op2, op):

    timeoutCnt = 0
    timeoutsAllowed = 3

    while True:
        try:
            if timeoutCnt == timeoutsAllowed:
                # To print the error message after three timeouts use:
                print("Error - No response after 3 attempts", flush=True)
                sys.exit()
            # Send data
            client_socket.send(f"{op1} {op2} {op}".encode())
            # To print the sending message when sending to the server use:
            print(f"Sending operation: {op1} {op2} {op}", flush=True)

            # Receive response
            data, addr = client_socket.recvfrom(1024)
            #print(f"Got response: {data.decode()}")
            break
        except socket.timeout:
            timeoutCnt += 1
            #print("No response received")
        except Exception as e:
            raise Exception(f"{str(e)}")
    #print(data.decode(), flush= True)
    return data.decode()


    # To print the final result for total value use:
    # try:
    #     print(f"Total: {int(operandStack.pop())}", flush=True)
    
    # except ValueError:
    #     print("Invalid expression", flush= True)

    




if __name__ == "__main__":
    client_socket = start_udp_client(sys.argv)
    #print(sys.argv[3], flush= True)
    send_udp_message(client_socket, 10, 11, 12)
