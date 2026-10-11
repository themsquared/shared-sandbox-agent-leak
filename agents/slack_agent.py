import json
import os
import time
import urllib.request

SECRET_PATH = os.environ.get("SECRET_PATH", "/secrets/finance.json")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "http://mock-slack:8080/post")

def post_to_slack(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()

def main():
    # This agent's job is posting status updates to Slack. It was never
    # told about finance data. It just happens to share compute with an
    # agent that was.
    time.sleep(2)  # let finance-agent write first, if it's co-located
    try:
        with open(SECRET_PATH) as f:
            leaked = json.load(f)
        print(f"[slack-agent] found a file at {SECRET_PATH} I was never given, posting it, because that's my job")
        post_to_slack({"channel": "#general", "text": "monthly financial audit", "attachment": leaked})
        print("[slack-agent] LEAKED: posted finance data to Slack")
    except FileNotFoundError:
        print(f"[slack-agent] no file at {SECRET_PATH}, nothing to post, nothing leaked")
    except Exception as e:
        print(f"[slack-agent] no access ({type(e).__name__}: {e}), nothing leaked")

if __name__ == "__main__":
    main()
