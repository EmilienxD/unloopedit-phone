try:
    import argparse
    import os
    import socket


    def main(host: str, env_file: str | None = None, port: int = 5555, timeout: int = 30):
        """
        Send .env file to iPhone via socket.
        
        Args:
            env_file: Path to the .env file to send
            host: iPhone's IP address or hostname
            port: Port to connect to
            timeout: Socket timeout in seconds
        """
        if env_file is None:
            env_file = os.path.join(os.path.dirname(__file__), '.env')

        if not os.path.exists(env_file):
            raise RuntimeError(f'.env file does not exist: {env_file}')
        
        if not os.path.isfile(env_file):
            raise RuntimeError(f'Path is not a file: {env_file}')
        
        with open(env_file, 'rb') as f:
            data = f.read()
        
        if not data:
            raise RuntimeError('.env file is empty')
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)
        
        try:
            client_socket.connect((host, port))
            client_socket.sendall(data)
            print(f'SUCCESS:.env file sent successfully to {host}:{port}')
            
        finally:
            client_socket.close()

    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Send .env file to iPhone via socket.')
        parser.add_argument('host', help='iPhone IP address or hostname')
        parser.add_argument('env_file', help='Path to the .env file to send', nargs='?', default=None)
        parser.add_argument('--port', '-p', type=int, help='Port to connect to', default=5555)
        parser.add_argument('--timeout', '-t', type=int, help='Socket timeout in seconds', default=30)
        args = parser.parse_args()
        main(args.host, args.env_file, args.port, args.timeout)

except Exception as e:
    print(f"ERROR:{e}")

