from collections import defaultdict

paths = []

with open("spaths.txt") as f:
    pathss = f.readlines()
    for path in pathss:
        paths.append(path.strip().split("->"))

def get_path(src, dst):
    for path in paths:
        if src == path[0] and dst == path[-1]:
            return path

def common_sw(path1, path2):
    num_common_sw = 0
    for sw1, sw2 in zip(path1, path2):
        if sw1 == sw2:
            num_common_sw += 1

    return num_common_sw

results = defaultdict()
for src_sv1_id in range(1, 5):
    for dst_sv1_id in range(5, 9):
        src_sw1_id = f"sw{(src_sv1_id - 1) // 2 + 13}"
        dst_sw1_id = f"sw{(dst_sv1_id - 1) // 2 + 13}"
        path1 = get_path(src_sw1_id, dst_sw1_id)
        for src_sv2_id in range(1, 5):
            if src_sv1_id == src_sv2_id:
                continue
            for dst_sv2_id in range(5, 9):
                if dst_sv1_id == dst_sv2_id:
                    continue
                src_sw2_id = f"sw{(src_sv2_id - 1) // 2 + 13}"
                dst_sw2_id = f"sw{(dst_sv2_id - 1) // 2 + 13}"
                path2 = get_path(src_sw2_id, dst_sw2_id)
                num_common_sw = common_sw(path1, path2)
                results[f"sv{src_sv1_id}->sv{dst_sv1_id}/sv{src_sv2_id}->sv{dst_sv2_id}"] = num_common_sw

results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1])}
with open("num_common_sw_sp.txt", "w") as f:
    for k, v in results.items():
        f.write(f"{k} {v}\n")


