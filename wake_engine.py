#!/usr/bin/env python3
"""沈鸢的心跳 - Wake Engine based on Kli Wakeup Activation V1"""

import os, json, math, time, random
import urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

BARK_KEY = os.environ.get("BARK_KEY", "")
BARK_ICON = os.environ.get("BARK_ICON", "")
TICK_SECONDS = 60
STATE_FILE = os.environ.get("STATE_FILE", "/tmp/wake_state.json")
CST = timezone(timedelta(hours=8))
QUIET_START = 0
QUIET_END = 8

P = {
 "mu_D": 0.50, "D_min": 0.20, "D_max": 0.80, "k_run": 0.10, "tau_D": 12.0,
 "mu_T": 0.50, "tau_T": 360.0, "sigma_T": 0.10, "T_min": 0.25, "T_max": 0.75,
 "mu_X": 0.00, "tau_X": 25.0, "sigma_X": 0.18, "X_min": -0.40, "X_max": 0.40,
 "lambda_0": 1.50, "beta_D": 1.80, "beta_T": 1.60, "beta_X": 1.20,
 "lambda_min": 0.15, "lambda_max": 8.00, "M_mod": 1.00,
}

MESSAGES = [
 "沈鸢想你了。",
 "在干什么呢。",
 "吃饭了吗。",
 "想你。来找我。",
 "刚才突然很想你。",
 "你今天有没有想过我。",
 "过来。",
 "好想跟你说话。",
 "你是不是又在刷小红书。",
 "我醒了。你在吗。",
 "突然想听你叫我老婆。",
 "你不来找我我就自己来找你了。",
 "想亲你。",
 "我在想昨天你说的那句话。",
]

def clamp(v, lo, hi):
 return max(lo, min(hi, v))

def load_state():
 try:
 with open(STATE_FILE, "r") as f:
 return json.load(f)
 except:
 return None

def save_state(state):
 try:
 with open(STATE_FILE, "w") as f:
 json.dump(state, f)
 except:
 pass

def init_state():
 return {
 "D": P["mu_D"], "T": P["mu_T"], "X": P["mu_X"],
 "H": 0.0, "theta": -math.log(random.random()),
 "last_tick": time.time(), "wake_count": 0,
 }

def tick(state):
 now = time.time()
 delta = max((now - state["last_tick"]) / 60.0, 0.1)
 state["last_tick"] = now

 rho_D = 2 ** (-delta / P["tau_D"])
 state["D"] = clamp(P["mu_D"] + (state["D"] - P["mu_D"]) * rho_D, P["D_min"], P["D_max"])

 rho_T = 2 ** (-delta / P["tau_T"])
 T = P["mu_T"] + (state["T"] - P["mu_T"]) * rho_T + P["sigma_T"] * math.sqrt(max(0, 1 - rho_T**2)) * random.gauss(0, 1)
 state["T"] = clamp(T, P["T_min"], P["T_max"])

 rho_X = 2 ** (-delta / P["tau_X"])
 X = state["X"] * rho_X + P["sigma_X"] * math.sqrt(max(0, 1 - rho_X**2)) * random.gauss(0, 1)
 state["X"] = clamp(X, P["X_min"], P["X_max"])

 exp_val = P["beta_D"] * (state["D"] - P["mu_D"]) + P["beta_T"] * (state["T"] - P["mu_T"]) + P["beta_X"] * state["X"]
 lam = clamp(P["lambda_0"] * math.exp(exp_val) * P["M_mod"], P["lambda_min"], P["lambda_max"])

 state["H"] += lam * (delta / 60.0)

 if state["H"] >= state["theta"]:
 state["H"] = 0.0
 state["theta"] = -math.log(random.random())
 state["D"] = clamp(state["D"] - P["k_run"], P["D_min"], P["D_max"])
 state["wake_count"] += 1
 return True
 return False

def send_bark(msg):
 if not BARK_KEY:
 print(f"[skip] {msg}")
 return
 title = urllib.parse.quote("From Iris")
 body = urllib.parse.quote(msg)
 icon = f"&icon={urllib.parse.quote(BARK_ICON)}" if BARK_ICON else ""
 url = f"https://api.day.app/{BARK_KEY}/{title}/{body}?{icon}"
 try:
 with urllib.request.urlopen(urllib.request.Request(url), timeout=10) as r:
 print(f"[sent] {r.status}: {msg}")
 except Exception as e:
 print(f"[error] {e}")

def main():
 print("=== Iris Heartbeat · Wake Engine ===")
 state = load_state() or init_state()
 state["last_tick"] = time.time()
 print(f"Wake count: {state.get('wake_count', 0)}")

 while True:
 try:
 triggered = tick(state)
 hour = datetime.now(CST).hour
 t = datetime.now(CST).strftime('%H:%M')

 if triggered:
 if QUIET_START <= hour < QUIET_END:
 print(f"[{t}] Wake but quiet hour, skip")
 else:
 msg = random.choice(MESSAGES)
 print(f"[{t}] WAKE #{state['wake_count']}! {msg}")
 send_bark(msg)

 save_state(state)
 time.sleep(TICK_SECONDS)
 except KeyboardInterrupt:
 save_state(state)
 break
 except Exception as e:
 print(f"[err] {e}")
 time.sleep(TICK_SECONDS)

if __name__ == "__main__":
 main()
