import os
import re
import json
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for, send_file
from collections import defaultdict

app = Flask(__name__)

# Configuration
DATA_DIR = "."  # Set this to the root directory of your data
DARK_BG = "#1E1E1E"
CUSTOM_NAMES_FILE = "dataset_names.json"  # File to store custom dataset names

def load_custom_names():
    """Load custom dataset names from JSON file."""
    names_path = os.path.join(DATA_DIR, CUSTOM_NAMES_FILE)
    if os.path.exists(names_path):
        try:
            with open(names_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {CUSTOM_NAMES_FILE}, using empty dictionary")
    return {}

def save_custom_names(names):
    """Save custom dataset names to JSON file."""
    names_path = os.path.join(DATA_DIR, CUSTOM_NAMES_FILE)
    with open(names_path, 'w') as f:
        json.dump(names, f, indent=2)

def parse_experiment_id(filename):
    """Extract experiment ID (e.g., EB20) from filename."""
    match = re.search(r'(EB\d+)', filename)
    if match:
        return match.group(1)
    return None

def parse_condition(filename):
    """Extract condition from filename (e.g., PD_AR_WD-vs-AR_MK)."""
    match = re.search(r'((?:_[^_]+)?_[^\.]+)\.html$', filename)
    if match:
        return match.group(1).lstrip('_')
    return None

def organize_plots():
    """Scan directories and organize plots by experiment ID and conditions."""
    plots = defaultdict(lambda: defaultdict(list))
    experiment_counts = {}
    custom_names = load_custom_names()
    
    for root, dirs, files in os.walk(DATA_DIR):
        html_files = [f for f in files if f.endswith('.html')]
        
        for file in html_files:
            exp_id = parse_experiment_id(file)
            condition = parse_condition(file)
            
            if exp_id and condition:
                rel_path = os.path.relpath(os.path.join(root, file), DATA_DIR)
                category_match = re.search(r'(?:CTLH-related|total-proteome|overview|UBE2H-PD|ARMC8-PD|PD|rec-GID-PD|E3ome|Proteasome)', file)
                category = category_match.group(0) if category_match else "other"
                
                plots[exp_id][category].append({
                    'filename': file,
                    'path': rel_path,
                    'condition': condition,
                    'is_overview': 'overview' in file.lower(),
                    'is_heatmap': 'heatmap' in file.lower()
                })
                
                if exp_id in experiment_counts:
                    experiment_counts[exp_id] += 1
                else:
                    experiment_counts[exp_id] = 1
    
    # Sort experiments by number (newest first)
    sorted_experiments = sorted(plots.keys(), 
                              key=lambda x: int(re.search(r'EB(\d+)', x).group(1)), 
                              reverse=True)
    
    return plots, sorted_experiments, experiment_counts, custom_names

def get_raw_data_path(exp_id):
    """Get path to raw data Excel file for a given experiment ID."""
    # Raw data is one folder up from the current directory
    raw_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    raw_data_file = f"{exp_id}_raw.xlsx"
    raw_data_path = os.path.join(raw_data_dir, raw_data_file)
    
    if os.path.exists(raw_data_path):
        return raw_data_path
    return None

@app.route('/')
def index():
    plots, sorted_experiments, exp_counts, custom_names = organize_plots()
    
    # Group experiment IDs for better navigation
    experiment_groups = {}
    for exp in sorted_experiments:
        exp_num = re.search(r'EB(\d+)', exp).group(1)
        first_digit = exp_num[0] if exp_num else '0'
        if first_digit not in experiment_groups:
            experiment_groups[first_digit] = []
        experiment_groups[first_digit].append(exp)
    
    sorted_groups = sorted(experiment_groups.keys(), reverse=True)
    
    return render_template('index.html', 
                          plots=plots,
                          sorted_experiments=sorted_experiments,
                          experiment_groups=experiment_groups,
                          sorted_groups=sorted_groups,
                          exp_counts=exp_counts,
                          custom_names=custom_names,
                          dark_bg=DARK_BG)

@app.route('/experiment/<exp_id>')
def experiment_detail(exp_id):
    plots, sorted_experiments, _, custom_names = organize_plots()
    
    if exp_id not in plots:
        abort(404)
    
    # Get the categories for this experiment
    categories = list(plots[exp_id].keys())
    
    # Find neighboring experiments for navigation
    exp_index = sorted_experiments.index(exp_id) if exp_id in sorted_experiments else -1
    prev_exp = sorted_experiments[exp_index + 1] if exp_index < len(sorted_experiments) - 1 else None
    next_exp = sorted_experiments[exp_index - 1] if exp_index > 0 else None
    
    # Check if raw data file exists
    raw_data_available = get_raw_data_path(exp_id) is not None
    
    return render_template('experiment.html',
                          exp_id=exp_id,
                          categories=categories,
                          plots=plots[exp_id],
                          prev_exp=prev_exp,
                          next_exp=next_exp,
                          custom_names=custom_names,
                          dark_bg=DARK_BG,
                          raw_data_available=raw_data_available)

@app.route('/view/<path:file_path>')
def view_plot(file_path):
    """Serve the HTML file for viewing."""
    directory, filename = os.path.split(file_path)
    return send_from_directory(os.path.join(DATA_DIR, directory), filename)

@app.route('/download_raw/<exp_id>')
def download_raw_data(exp_id):
    """Serve the raw data Excel file for download."""
    raw_data_path = get_raw_data_path(exp_id)
    
    if raw_data_path:
        directory, filename = os.path.split(raw_data_path)
        return send_file(raw_data_path, 
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True,
                        download_name=filename)
    else:
        abort(404)

@app.route('/update_name/<exp_id>', methods=['POST'])
def update_dataset_name(exp_id):
    """Update the custom name for a dataset."""
    custom_names = load_custom_names()
    custom_name = request.form.get('custom_name', '').strip()
    
    if custom_name:
        custom_names[exp_id] = custom_name
    elif exp_id in custom_names:
        # If the name is empty, remove it from the dictionary
        del custom_names[exp_id]
    
    save_custom_names(custom_names)
    
    # Redirect back to the referring page
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Choose an unused port, like 5002
    port = 5002
    
    print(f"Listening on IP: {local_ip}")
    print(f"Listening on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)