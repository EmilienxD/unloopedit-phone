from sys import platform
if platform != 'darwin':
    raise RuntimeError('This code is only dedicated for an iphone darwin virtuel machine')

try:
    import argparse
    import os
    import socket


    def main(folder: str, port: int = 5555, host: str = '0.0.0.0', timeout: int = 30):
        """
        Receive .env file via socket and save it to the project folder.
        
        Args:
            folder: The project folder where .env should be saved
            port: Port to listen on
            host: Host address to bind to
            timeout: Socket timeout in seconds
        """
        env_path = os.path.join(folder, '.env')
        
        if not os.path.exists(folder):
            raise RuntimeError(f'Folder does not exist: {folder}')
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(timeout)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(1)
            
            conn, addr = server_socket.accept()
            
            try:
                data = b''
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                
                if not data:
                    raise RuntimeError('No data received from sender')
                
                with open(env_path, 'wb') as f:
                    f.write(data)
                
                print(f'SUCCESS:.env file received and saved to {env_path}', end='')
                
            finally:
                conn.close()
                
        finally:
            server_socket.close()

    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Receive .env file via socket for iPhone project.')
        parser.add_argument('folder', help='The project folder where .env should be saved')
        parser.add_argument('--port', '-p', type=int, help='Port to listen on', default=5555)
        parser.add_argument('--host', help='Host address to bind to', default='0.0.0.0')
        parser.add_argument('--timeout', '-t', type=int, help='Socket timeout in seconds', default=30)
        args = parser.parse_args()
        main(args.folder, args.port, args.host, args.timeout)

except Exception as e:
    print(f"ERROR:{e}", end='')

