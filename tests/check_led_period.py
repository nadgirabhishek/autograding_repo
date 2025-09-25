import sys, re, statistics

TARGET_HALF_MS = 500.0
TOL_MS = 50.0         # +/-10%
MIN_EDGES, MAX_EDGES = 16, 26   # ~20 edges over 10s (allow slack)

def parse_times(path):
    t_ms, v = [], []
    with open(path) as f:
        for line in f:
            # Match "123.4ms ... 1" OR "1.234s ... 0"
            m = re.search(r'(\d+(?:\.\d+)?)(ms|s).*?\b([01])\b', line)
            if m:
                t = float(m.group(1))
                if m.group(2) == 's':
                    t *= 1000.0
                t_ms.append(t)
                v.append(int(m.group(3)))
    return t_ms, v

path = "out/renode_gpio_log.csv"
t, v = parse_times(path)
if not t:
    print(f"FAIL: no GPIO samples in {path}")
    sys.exit(1)

edges = [t[i] for i in range(1, len(v)) if v[i] != v[i-1]]
if not (MIN_EDGES <= len(edges) <= MAX_EDGES):
    print(f"FAIL: expected ~20 edges in 10s, got {len(edges)}")
    sys.exit(1)

half = [edges[i+1] - edges[i] for i in range(len(edges)-1)]
bad = [h for h in half if abs(h - TARGET_HALF_MS) > TOL_MS]
if bad:
    print(f"FAIL: {len(bad)} half-period(s) outside {TARGET_HALF_MS}±{TOL_MS} ms")
    print("Half-periods (ms) sample:", [round(x,1) for x in half[:10]])
    sys.exit(1)

print(f"PASS: mean half-period = {statistics.mean(half):.1f} ms; edges={len(edges)}")
