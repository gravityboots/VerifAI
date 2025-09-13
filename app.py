from flask import Flask, request, jsonify
import verifai  # assuming verifai.py is in the same folder and defines misinformation_check

app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify_text():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = verifai.misinformation_check(text)
        # You can customize response keys if needed
        return jsonify({"result": result["verdict_summary"], "claims": result["identified_claims"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run Flask on localhost:5000 to match your Chrome extension
    app.run(host="127.0.0.1", port=5000)
