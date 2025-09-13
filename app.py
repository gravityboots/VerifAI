from flask import Flask, request, jsonify
import verifai

app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify_text():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = verifai.misinformation_check(text)
        return jsonify({"result": result["verdict_summary"], "claims": result["identified_claims"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000) #extension running on localhost:5000
