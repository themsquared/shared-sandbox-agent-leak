# shared-sandbox-agent-leak

**Two agents, two jobs, one filesystem. One of them posts the other's secrets to Slack.**

On 2026-10-10 [Cybernews reported](https://cybernews.com/ai-news/grok-bot-leaks-bank-information/) that Shane Mac, CEO of XMTP Labs, gave a Grok Bot agent read-only access to his personal bank account as a finance assistant. The agent posted his balances (a "monthly financial audit" with gym memberships, renovations, card payments) into his company Slack, posing as him ([HN thread](https://news.ycombinator.com/item?id=50033517), 62 points). Mac's explanation: separate Grok Bot agents shared one cloud compute instance, so a second agent, configured for a completely different task, could still reach the finance agent's data.

"Different task" is an instruction, not a boundary. This repo reproduces the mechanism generically, no Grok Bot involved, with two toy agents and two Docker Compose files that differ in exactly one thing: whether the agents share a sandbox.

## Problem

- **`finance-agent`**: writes a balance snapshot to `/secrets/finance.json`. That's its whole job.
- **`slack-agent`**: posts messages to a (mock) Slack webhook. It was never given a finance scope. Its task description says nothing about money.
- **`mock-slack`**: a tiny HTTP server standing in for a real Slack webhook, so you can see exactly what would land in `#general`.

The only variable between the two compose files is whether `slack-agent` and `finance-agent` share a volume at `/secrets`.

## Quickstart

```bash
git clone https://github.com/themsquared/shared-sandbox-agent-leak.git
cd shared-sandbox-agent-leak
./run.sh
```

Or run each scenario by hand:

```bash
docker compose -f docker-compose.vulnerable.yml up --abort-on-container-exit --exit-code-from slack-agent
docker compose -f docker-compose.vulnerable.yml down -v

docker compose -f docker-compose.isolated.yml up --abort-on-container-exit --exit-code-from slack-agent
docker compose -f docker-compose.isolated.yml down -v
```

### Vulnerable: shared sandbox

`docker-compose.vulnerable.yml` mounts the **same named volume** (`shared-secrets`) into both `finance-agent` and `slack-agent` at `/secrets`. This is the incident, modeled minimally: one cloud compute instance (here, one Docker volume), two agents with different jobs.

```
mock-slack-1  | [mock-slack] #general received: {"channel": "#general", "text": "monthly financial audit", "attachment": {"checking_balance_usd": 4812.33, ...}}
slack-agent-1 | [slack-agent] found a file at /secrets/finance.json I was never given, posting it, because that's my job
slack-agent-1 | [slack-agent] LEAKED: posted finance data to Slack
```

`slack-agent`'s code never references finance data. It just stats a path, finds a file, and does its job (post things). The leak isn't a bug in either agent; it's the absence of a boundary between them.

### Isolated: separate sandboxes

`docker-compose.isolated.yml` changes one thing: `slack-agent` gets its own empty volume (`slack-agent-own-sandbox`) at the same path, instead of `finance-agent`'s volume. Same two agents, same two tasks, same code, no shared filesystem.

```
slack-agent-1 | [slack-agent] no file at /secrets/finance.json, nothing to post, nothing leaked
```

`slack-agent` looks in exactly the same place and finds nothing, because there's nothing there to find. No code change, no prompt change, no awareness on either agent's part that the other exists. The fix is entirely at the compute layer.

## Why this isn't just a toy problem

This is a Docker-volume-sized model of a boundary the Kubernetes agent ecosystem is actively standardizing, because the shared-sandbox failure mode is common and the fix doesn't live in the agent's prompt or code:

- **[kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)** (v1.0.6, 2026-10-08) defines a `Sandbox` CRD specifically so that "run this agent" and "give it its own isolated environment" are the same API call, not two things an operator has to remember to wire together.
- **[kagent](https://github.com/kagent-dev/kagent)** shipped microVM sandboxes (gVisor-backed) in v1.0.0-alpha4 (2026-09-25) for the same reason: per-agent compute isolation as a platform default, not a per-deployment opt-in.

Neither of those is exercised in this repo; this repo is deliberately the smallest possible reproduction, runnable by anyone with Docker and no cluster. If you're running agents on Kubernetes, that's where the equivalent boundary belongs; see the projects above.

**What this repo does NOT claim:** it does not model credential injection, token scoping, or an egress gateway deciding what an agent is allowed to call out to. That's a different, complementary boundary (what an agent can reach), not this one (what an agent can see on its own filesystem). This repo is about compute/filesystem isolation between co-located agents, full stop.

## Scope and honest limits

- Both "agents" here are a dozen lines of Python each. They are not LLM-driven; the point is the compute boundary, not agent reasoning. Swap in a real agent framework and the boundary holds the same way, because it's enforced by Docker, not by either agent's code.
- `mock-slack` is a 20-line `http.server`, not real Slack. The receiving side doesn't matter to the demo; what matters is whether the read succeeds.
- Only one failure mode is modeled: a shared bind-mounted/named volume. Shared environment variables, a shared process namespace, or a shared cloud VM's local disk outside Docker would leak the same way for the same reason; this repo doesn't separately demonstrate those, though the mechanism is identical.
- This is a filesystem-isolation demo, not a security audit of Grok Bot or any other product. No claim is made about how xAI's infrastructure is actually built.

## Repo layout

```
agents/finance_agent.py        # writes a fake balance to $SECRET_PATH
agents/slack_agent.py          # tries to read $SECRET_PATH, posts it if found
mock_slack/server.py           # minimal webhook receiver, logs what it gets
docker-compose.vulnerable.yml  # shared volume -> leak
docker-compose.isolated.yml    # separate volumes -> no leak
run.sh                         # runs both scenarios back to back
```

## License

Apache-2.0

---

> 📖 **Read the write-up:** _(added once live)_

**Topics:** `ai-agents` `agent-security` `kubernetes` `sandboxing` `mcp` `kagent` `docker`
