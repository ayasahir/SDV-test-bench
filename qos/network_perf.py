#!/usr/bin/env python3
"""
Network Performance and QoS Testing App
Measures latency, throughput, and reliability while transferring images
between Raspberry Pi devices over Ethernet.
"""

import socket
import threading
import time
import os
import struct
import hashlib
import json
import argparse
from datetime import datetime

class NetworkPerformanceTester:
    def __init__(self, host='0.0.0.0', port=8888, buffer_size=4096):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.results = {
            'transfer_time': 0,
            'throughput_mbps': 0,
            'latency_ms': 0,
            'packet_loss': 0,
            'file_integrity': False,
            'timestamp': None
        }
    
    def calculate_checksum(self, data):
        """Calculate MD5 checksum for data integrity verification"""
        return hashlib.md5(data).hexdigest()
    
    def ping_test(self, target_ip, count=10):
        """Simple ping test to measure basic latency"""
        import subprocess
        try:
            cmd = f"ping -c {count} {target_ip}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Parse ping results
            lines = result.stdout.split('\n')
            for line in lines:
                if 'avg' in line:
                    # Extract average latency
                    parts = line.split('=')[1].split('/')
                    avg_latency = float(parts[1])
                    return avg_latency
        except Exception as e:
            print(f"Ping test failed: {e}")
            return 0
        return 0
    
    def server_mode(self, save_path="received_image.jpg"):
        """Run as server to receive image and measure performance"""
        print(f"Starting server on {self.host}:{self.port}")
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        
        print("Waiting for connection...")
        
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connected to {addr}")
            
            try:
                # Receive metadata first
                metadata_size = struct.unpack('!I', client_socket.recv(4))[0]
                metadata_json = client_socket.recv(metadata_size).decode('utf-8')
                metadata = json.loads(metadata_json)
                
                file_size = metadata['file_size']
                original_checksum = metadata['checksum']
                start_time = metadata['start_time']
                
                print(f"Receiving file: {metadata['filename']} ({file_size} bytes)")
                
                # Receive file data
                received_data = b''
                bytes_received = 0
                receive_start = time.time()
                
                while bytes_received < file_size:
                    chunk = client_socket.recv(min(self.buffer_size, file_size - bytes_received))
                    if not chunk:
                        break
                    received_data += chunk
                    bytes_received += len(chunk)
                
                receive_end = time.time()
                
                # Calculate metrics
                transfer_time = receive_end - start_time
                throughput_mbps = (file_size * 8) / (transfer_time * 1_000_000)  # Mbps
                received_checksum = self.calculate_checksum(received_data)
                file_integrity = (original_checksum == received_checksum)
                
                # Save received file
                with open(save_path, 'wb') as f:
                    f.write(received_data)
                
                # Update results
                self.results.update({
                    'transfer_time': round(transfer_time, 3),
                    'throughput_mbps': round(throughput_mbps, 2),
                    'file_integrity': file_integrity,
                    'bytes_received': bytes_received,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send acknowledgment with results
                response = json.dumps(self.results)
                client_socket.send(response.encode('utf-8'))
                
                self.print_results()
                
            except Exception as e:
                print(f"Error receiving file: {e}")
            finally:
                client_socket.close()
    
    def client_mode(self, target_ip, image_path):
        """Run as client to send image and measure performance"""
        if not os.path.exists(image_path):
            print(f"Error: Image file {image_path} not found")
            return False
        
        print(f"Connecting to {target_ip}:{self.port}")
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            file_size = len(file_data)
            checksum = self.calculate_checksum(file_data)
            
            # Ping test for latency measurement
            latency = self.ping_test(target_ip)
            self.results['latency_ms'] = round(latency, 2)
            
            # Connect to server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((target_ip, self.port))
            
            start_time = time.time()
            
            # Send metadata
            metadata = {
                'filename': os.path.basename(image_path),
                'file_size': file_size,
                'checksum': checksum,
                'start_time': start_time
            }
            
            metadata_json = json.dumps(metadata)
            metadata_bytes = metadata_json.encode('utf-8')
            client_socket.send(struct.pack('!I', len(metadata_bytes)))
            client_socket.send(metadata_bytes)
            
            # Send file data
            bytes_sent = 0
            while bytes_sent < file_size:
                chunk = file_data[bytes_sent:bytes_sent + self.buffer_size]
                sent = client_socket.send(chunk)
                bytes_sent += sent
            
            print(f"Sent {bytes_sent} bytes")
            
            # Receive results from server
            response = client_socket.recv(1024).decode('utf-8')
            server_results = json.loads(response)
            
            # Merge results
            self.results.update(server_results)
            
            client_socket.close()
            
            self.print_results()
            return True
            
        except Exception as e:
            print(f"Error sending file: {e}")
            return False
    
    def print_results(self):
        """Print formatted performance results"""
        print("\n" + "="*50)
        print("NETWORK PERFORMANCE RESULTS")
        print("="*50)
        print(f"Transfer Time:     {self.results['transfer_time']:.3f} seconds")
        print(f"Throughput:        {self.results['throughput_mbps']:.2f} Mbps")
        print(f"Latency:           {self.results['latency_ms']:.2f} ms")
        print(f"File Integrity:    {'✓ PASS' if self.results['file_integrity'] else '✗ FAIL'}")
        print(f"Bytes Transferred: {self.results.get('bytes_received', 0):,}")
        print(f"Timestamp:         {self.results['timestamp']}")
        print("="*50)
    
    def save_results(self, filename="network_performance_log.json"):
        """Save results to JSON file for analysis"""
        try:
            # Load existing results
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    all_results = json.load(f)
            else:
                all_results = []
            
            # Append new results
            all_results.append(self.results)
            
            # Save updated results
            with open(filename, 'w') as f:
                json.dump(all_results, f, indent=2)
            
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Network Performance and QoS Tester')
    parser.add_argument('mode', choices=['server', 'client'], help='Run as server or client')
    parser.add_argument('--host', default='0.0.0.0', help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, help='Port number (default: 8888)')
    parser.add_argument('--target', help='Target IP address (client mode only)')
    parser.add_argument('--image', help='Image file path (client mode only)')
    parser.add_argument('--save-path', default='received_image.jpg', help='Save path for received image (server mode)')
    parser.add_argument('--buffer-size', type=int, default=4096, help='Buffer size (default: 4096)')
    parser.add_argument('--log', default='network_performance_log.json', help='Log file path')
    
    args = parser.parse_args()
    
    tester = NetworkPerformanceTester(args.host, args.port, args.buffer_size)
    
    try:
        if args.mode == 'server':
            tester.server_mode(args.save_path)
        elif args.mode == 'client':
            if not args.target or not args.image:
                print("Error: Client mode requires --target and --image arguments")
                return
            
            success = tester.client_mode(args.target, args.image)
            if success:
                tester.save_results(args.log)
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()