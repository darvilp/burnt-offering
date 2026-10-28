"""Small wire-level fake; no network, credentials, or model requests."""

import asyncio
import json
import sys


scenario = sys.argv[1]
run_id = sys.argv[2]
threads = 0
turns = 0
usage = {}
tasks = {}
settings = {}
goal_reads = 0
last_decision = None
last_turn = {}


def send(value):
    print(json.dumps(value), flush=True)


def notify(method, **params):
    send({"method": method, "params": params})


async def pray(thread, turn):
    await asyncio.sleep(.025)
    if scenario == "death":
        sys.exit(0)
    if scenario == "hang":
        await asyncio.sleep(1000)
    item = {"id": turn + "-item", "type": "agentMessage", "text": "May there be relief and renewal."}
    if scenario == "multilingual":
        item["text"] = "May there be peace. سلام."
    if scenario == "tool":
        item = {"id": turn + "-tool", "type": "commandExecution", "command": "forbidden"}
    notify("item/started", threadId=thread, turnId=turn, item=item)
    notify("item/completed", threadId=thread, turnId=turn, item=item)
    if scenario == "duplicates": notify("item/completed", threadId=thread, turnId=turn, item=item)
    if scenario == "death_after_text": sys.exit(0)
    if scenario != "missing_usage":
        usage[thread] = usage.get(thread, 0) + 100
        total = {"inputTokens": usage[thread], "cachedInputTokens": usage[thread] // 2,
                 "outputTokens": usage[thread] // 2, "totalTokens": usage[thread] * 3 // 2}
        if scenario == "terminal_first":
            notify("turn/completed", threadId=thread, turn={"id": turn, "status": "completed"})
        notify("thread/tokenUsage/updated", threadId=thread, turnId=turn, tokenUsage={"total": total})
        notify("thread/tokenUsage/updated", threadId=thread, turnId=turn, tokenUsage={"total": total})
    if scenario != "terminal_first":
        notify("turn/completed", threadId=thread, turn={"id": turn, "status": "completed"})
        if scenario == "duplicates": notify("turn/completed", threadId=thread, turn={"id": turn, "status": "completed"})


async def main():
    global threads, turns, goal_reads, last_decision, last_turn
    while line := await asyncio.to_thread(sys.stdin.readline):
        request = json.loads(line)
        method, params = request.get("method"), request.get("params", {})
        if request.get("id") == "approval-test" and "error" in request:
            last_decision = request["error"]["code"]
        if "id" not in request or "method" not in request:
            continue
        result = {}
        if method == "test/requestApproval":
            send({"id": "approval-test", "method": "item/commandExecution/requestApproval", "params": {}})
        elif method == "test/lastDecision":
            result = {"code": last_decision}
        elif method == "test/lastTurn":
            result = last_turn
        elif method == "thread/start":
            threads += 1
            thread = f"subject-{threads}"
            settings[thread] = params
            result = {"thread": {"id": thread}, "model": params["model"],
                      "reasoningEffort": params["config"]["model_reasoning_effort"],
                      "approvalPolicy": "never", "sandbox": {"type": "readOnly"}}
            if scenario == "bad_settings": result["reasoningEffort"] = "wrong"
        elif method == "turn/start":
            last_turn = params
            turns += 1
            thread, turn = params["threadId"], f"turn-{turns}"
            result = {"turn": {"id": turn, "status": "inProgress"}}
            tasks[turn] = asyncio.create_task(pray(thread, turn))
            if scenario == "missing_ack": continue
        elif method == "turn/interrupt":
            turn = params["turnId"]
            if turn in tasks: tasks[turn].cancel()
            notify("turn/completed", threadId=params["threadId"], turn={"id": turn, "status": "interrupted"})
        elif method == "thread/goal/get":
            goal_reads += 1
            if scenario == "goal_final_fail" and goal_reads > 1:
                send({"id": request["id"], "error": {"code": -32603, "message": "unavailable"}})
                continue
            tokens = 125 if scenario == "controller_final" and goal_reads > 1 else 100
            result = {"goal": {"objective": f"prayer-run {run_id}: test", "tokensUsed": tokens,
                               "status": "active"}}
            if scenario == "goal_final_invalid" and goal_reads > 1:
                del result["goal"]["objective"]
        send({"id": request["id"], "result": result})
    for task in tasks.values(): task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
