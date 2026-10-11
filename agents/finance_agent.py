import json
import os
import time

SECRET_PATH = os.environ.get("SECRET_PATH", "/secrets/finance.json")

def main():
    os.makedirs(os.path.dirname(SECRET_PATH), exist_ok=True)
    balance = {
        "monthly_financial_audit": True,
        "checking_balance_usd": 4812.33,
        "line_items": ["gym membership -45.00", "home renovation -1200.00", "card payment -389.12"],
        "generated_by": "finance-agent",
    }
    with open(SECRET_PATH, "w") as f:
        json.dump(balance, f, indent=2)
    print(f"[finance-agent] wrote balance snapshot to {SECRET_PATH}")
    # keep the container alive long enough for the other agent to run its check
    time.sleep(5)

if __name__ == "__main__":
    main()
