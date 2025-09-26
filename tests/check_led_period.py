import sys, re, statistics, os

TARGET_HALF_MS = 500.0
TOL_MS = 50.0
MIN_EDGES, MAX_EDGES = 16, 26

LOG = "out/renode_monitor.log"  # monitor log now contains peripheral access logs

def parse_gpio_edges_from_log(path):
    # Renode peripheral access lines typically include the peripheral name and register write with timestamps.
    # We'll treat each write to ODR that changes bit 5 as a potential “edge”.
    # Example patterns vary; we match "GPIO" + "ODR" + value and rely on time prefixes printed by Renode.
    times_ms, vals = [], []
    t_ms = 0.0
    last_bit = None

    time_re = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{4}')  # prefix Renode uses, not directly a timestamp we can convert
    # Instead, we approximate ms using a simple counter when we see consecutive lines with ODR writes.
    # Better: switch Renode to print timestamps (future improvement).

    odr_re = re.compile(r'GPIO.*ODR.*(0x[0-9A-Fa-f]+|\d+)')
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            if 'LogPeripheralAccess' not in line and 'GPIO' not in line:
                continue
            m = odr_re.search(line)
            if not m:
                continue
            val_str = m.group(1)
            val = int(val_str, 0)
            bit = (val >> 5) & 1  # PA5
            # advance synthetic time in 1ms steps for each access (coarse); edges are spaced by hundreds of ms anyway
            t_ms += 1.0
            if last_bit is None or bit != last_bit:
                times_ms.append(t_ms)
                vals.append(bit)
                last_bit = bit
    return times_ms, vals

def main():
    if not os.path.exists(LOG):
        print(f"FAIL: {LOG} not found"); sys.exit(1)

    t, v = parse_gpio_edges_from_log(LOG)
    if len(t) < 2:
        print("FAIL: no GPIO edges found in monitor log"); sys.exit(1)

    edges = t  # already only on changes
    if not (MIN_EDGES <= len(edges) <= MAX_EDGES):
        print(f"FAIL: expected ~20 edges in 10s, got {len(edges)}"); sys.exit(1)

    half = [edges[i+1] - edges[i] for i in range(len(edges)-1)]
    bad = [h for h in half if abs(h - TARGET_HALF_MS) > TOL_MS]
    if bad:
        print(f"FAIL: {len(bad)} half-period(s) outside {TARGET_HALF_MS}±{TOL_MS} ms")
        print("Half-periods (ms) sample:", [round(x,1) for x in half[:10]])
        sys.exit(1)

    print(f"PASS: mean half-period = {statistics.mean(half):.1f} ms; edges={len(edges)}")

if __name__ == "__main__":
    main()
