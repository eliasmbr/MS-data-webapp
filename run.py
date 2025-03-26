#!/usr/bin/env python3
"""
Run script for Experimental Data Viewer
"""
import os
import sys
from app import app

if __name__ == "__main__":
    # Check if a specific data directory was provided as an argument
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        if os.path.isdir(data_dir):
            app.config["DATA_DIR"] = data_dir
            print(f"Using data directory: {data_dir}")
        else:
            print(f"Error: Directory '{data_dir}' not found.")
            sys.exit(1)
    
    # Print some helpful information
    print("=" * 50)
    print("Experimental Data Viewer")
    print("=" * 50)
    print(f"Data directory: {app.config.get('DATA_DIR', '.')}")
    
    # Count HTML files in data directory
    html_count = 0
    for root, _, files in os.walk(app.config.get('DATA_DIR', '.')):
        html_count += len([f for f in files if f.endswith('.html')])
    
    print(f"Found {html_count} HTML plot files")
    
    # Specify host and port explicitly
    host = '0.0.0.0'  # Listen on all network interfaces
    port = 5002
    
    print(f"\nAccess the application at: http://{host}:{port}")
    print("=" * 50)
    
    # Run the app with explicit host and port
    app.run(host=host, port=port, debug=True)