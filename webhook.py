from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Webhook Received")
    print(data)

    if 'events' in data:
        for event in data['events']:
            source = event.get('source', {})
            if source.get('type') == 'group':
                group_id = source.get('groupId')
                print(f"🎯 Group ID: {group_id}")
    
    return 'OK', 200

if __name__ == "__main__":
    app.run(port=5000)
