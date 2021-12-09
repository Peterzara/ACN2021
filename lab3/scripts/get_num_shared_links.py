from collections import defaultdict
import itertools
paths = []

with open("full_paths.txt") as f:
    pathss = f.readlines()
    for path in pathss:
        paths.append(path.strip().split("->"))

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def get_path(src, dst):
    for path in paths:
        if src == path[0] and dst == path[-1]:
            return path[1:-1]

def common_sw(path1, path2):
    num_common_links = 0
    for (sw1_a, sw1_b), (sw2_a, sw2_b) in zip(pairwise(path1), pairwise(path2)):
        if f"{sw1_a}-{sw1_b}" == f"{sw2_a}-{sw2_b}":
            num_common_links += 1

    return num_common_links

results = defaultdict()
for src_sv1_id in range(1, 5):
    for dst_sv1_id in range(5, 9):
        # src_sw1_id = f"sw{(src_sv1_id - 1) // 2 + 13}"
        # dst_sw1_id = f"sw{(dst_sv1_id - 1) // 2 + 13}"
        path1 = get_path(f"sv{src_sv1_id}", f"sv{dst_sv1_id}")
        for src_sv2_id in range(1, 5):
            if src_sv1_id == src_sv2_id:
                continue
            for dst_sv2_id in range(5, 9):
                if dst_sv1_id == dst_sv2_id:
                    continue
                # src_sw2_id = f"sw{(src_sv2_id - 1) // 2 + 13}"
                # dst_sw2_id = f"sw{(dst_sv2_id - 1) // 2 + 13}"
                path2 = get_path(f"sv{src_sv2_id}", f"sv{dst_sv2_id}")
                num_common_sw = common_sw(path1, path2)
                results[f"sv{src_sv1_id}->sv{dst_sv1_id}/sv{src_sv2_id}->sv{dst_sv2_id}"] = num_common_sw

results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1])}
with open("num_shared_links_ft.txt", "w") as f:
    for k, v in results.items():
        f.write(f"{k} {v}\n")


