"""
Simple Flask REST API for GitOps/CI/CD testing
"""
import os
import time
from datetime import datetime
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total request count', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['endpoint'])

# In-memory storage for demo
items = {}
item_counter = 0

# Configuration from environment
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
APP_ENV = os.getenv('APP_ENV', 'development')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Kubernetes liveness probe"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': APP_VERSION,
        'environment': APP_ENV
    }), 200


@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint for Kubernetes readiness probe"""
    return jsonify({
        'status': 'ready',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API info"""
    return jsonify({
        'name': 'GitOps Demo API',
        'version': APP_VERSION,
        'environment': APP_ENV,
        'endpoints': {
            'health': '/health',
            'ready': '/ready',
            'metrics': '/metrics',
            'items': '/api/items',
            'item_detail': '/api/items/<id>'
        }
    }), 200


@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items"""
    start_time = time.time()

    result = jsonify({
        'items': list(items.values()),
        'count': len(items)
    })

    REQUEST_LATENCY.labels(endpoint='/api/items').observe(time.time() - start_time)
    REQUEST_COUNT.labels(method='GET', endpoint='/api/items', status=200).inc()

    return result, 200


@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item"""
    global item_counter
    start_time = time.time()

    data = request.get_json()

    if not data or 'name' not in data:
        REQUEST_COUNT.labels(method='POST', endpoint='/api/items', status=400).inc()
        return jsonify({'error': 'Name is required'}), 400

    item_counter += 1
    item = {
        'id': item_counter,
        'name': data['name'],
        'description': data.get('description', ''),
        'created_at': datetime.utcnow().isoformat()
    }

    items[item_counter] = item

    REQUEST_LATENCY.labels(endpoint='/api/items').observe(time.time() - start_time)
    REQUEST_COUNT.labels(method='POST', endpoint='/api/items', status=201).inc()

    return jsonify(item), 201


@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a specific item"""
    start_time = time.time()

    if item_id not in items:
        REQUEST_COUNT.labels(method='GET', endpoint='/api/items/<id>', status=404).inc()
        return jsonify({'error': 'Item not found'}), 404

    REQUEST_LATENCY.labels(endpoint='/api/items/<id>').observe(time.time() - start_time)
    REQUEST_COUNT.labels(method='GET', endpoint='/api/items/<id>', status=200).inc()

    return jsonify(items[item_id]), 200


@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    start_time = time.time()

    if item_id not in items:
        REQUEST_COUNT.labels(method='PUT', endpoint='/api/items/<id>', status=404).inc()
        return jsonify({'error': 'Item not found'}), 404

    data = request.get_json()

    if not data:
        REQUEST_COUNT.labels(method='PUT', endpoint='/api/items/<id>', status=400).inc()
        return jsonify({'error': 'No data provided'}), 400

    item = items[item_id]
    item['name'] = data.get('name', item['name'])
    item['description'] = data.get('description', item['description'])
    item['updated_at'] = datetime.utcnow().isoformat()

    REQUEST_LATENCY.labels(endpoint='/api/items/<id>').observe(time.time() - start_time)
    REQUEST_COUNT.labels(method='PUT', endpoint='/api/items/<id>', status=200).inc()

    return jsonify(item), 200


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    start_time = time.time()

    if item_id not in items:
        REQUEST_COUNT.labels(method='DELETE', endpoint='/api/items/<id>', status=404).inc()
        return jsonify({'error': 'Item not found'}), 404

    del items[item_id]

    REQUEST_LATENCY.labels(endpoint='/api/items/<id>').observe(time.time() - start_time)
    REQUEST_COUNT.labels(method='DELETE', endpoint='/api/items/<id>', status=204).inc()

    return '', 204


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
