from flask import Flask, request, jsonify, send_from_directory
import os, requests

SERVING_URL = os.environ.get("SERVING_URL")  # Databricks serving invocations URL
DBRX_PAT    = os.environ.get("DBRX_PAT")     # Databricks PAT (server-side only)
ALLOW_ORIGIN= os.environ.get("ALLOW_ORIGIN", "*")

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Serve frontend files
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Handle other frontend routes (for client-side routing)
@app.route('/<path:path>')
def serve_other(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = ALLOW_ORIGIN
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

@app.route("/api/chat", methods=["POST","OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return ("", 204)
        
    if not SERVING_URL or not DBRX_PAT:
        return jsonify({"error": "Server configuration error: Missing SERVING_URL or DBRX_PAT"}), 500
    
    try:
        data = request.get_json(force=True)
        messages = data.get('messages', [])
        
        # Format the payload for Databricks
        payload = {
            "messages": messages,
            "temperature": data.get('temperature', 0.7),
            "max_tokens": data.get('max_tokens', 500),
        }
        
        # Make the request to Databricks
        response = requests.post(
            SERVING_URL,
            headers={
                "Authorization": f"Bearer {DBRX_PAT}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )
        
        # Forward the response
        return (response.text, response.status_code, {"Content-Type": "application/json"})
        
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))
