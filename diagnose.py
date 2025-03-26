import socket
import subprocess

def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False

def list_processes_using_port(port):
    try:
        # Windows command to find processes using the port
        result = subprocess.run(['netstat', '-ano', '|', 'findstr', f':{port}'], 
                                capture_output=True, text=True, shell=True)
        print(f"Processes using port {port}:")
        print(result.stdout)
    except Exception as e:
        print(f"Error listing processes: {e}")

# Check ports
ports_to_check = [5000, 5001, 5002]
for port in ports_to_check:
    print(f"\nChecking port {port}:")
    is_in_use = check_port(port)
    print(f"Port {port} in use: {is_in_use}")
    if is_in_use:
        list_processes_using_port(port)