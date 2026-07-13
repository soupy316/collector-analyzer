import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from parser import process_rvtools_workbook

app = Flask(__name__)
CORS(app) # Allow local UI calls

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('customers', exist_ok=True)

@app.route('/api/customers', methods=['GET'])
def list_customers():
    if not os.path.exists('customers'):
        return jsonify([])
    folders = [d for d in os.listdir('customers') if os.path.isdir(os.path.join('customers', d)) and not d.startswith('.')]
    return jsonify(sorted(folders))

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json or {}
    name = data.get('name', '').strip().replace(' ', '_')
    if not name:
        return jsonify({"error": "Name mandatory"}), 400
    os.makedirs(os.path.join('customers', name), exist_ok=True)
    return jsonify({"status": "created"})

@app.route('/api/clusters/<customer>', methods=['GET'])
def list_customer_clusters(customer):
    path = os.path.join('customers', customer)
    if not os.path.exists(path):
        return jsonify([])
    files = [f.replace('.json', '') for f in os.listdir(path) if f.endswith('.json')]
    return jsonify(sorted(files))

@app.route('/api/data/<customer>/<cluster>', methods=['GET'])
def get_cluster_data(customer, cluster):
    file_path = os.path.join('customers', customer, f"{cluster}.json")
    if not os.path.exists(file_path):
        return jsonify({"error": "Not found"}), 404
    with open(file_path, 'r') as f:
        import json
        return jsonify(json.load(f))

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file dropped"}), 400
    
    file = request.files['file']
    customer = request.form.get('customer')
    label = request.form.get('label', 'Cluster')

    if file.filename == '' or not customer:
        return jsonify({"error": "Missing assignment details"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Trigger processing engine
    result = process_rvtools_workbook(file_path, customer, label)
    
    # Remove file footprint reference from uploads once processed
    if os.path.exists(file_path):
        os.remove(file_path)

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)