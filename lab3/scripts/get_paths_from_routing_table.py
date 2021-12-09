paths_list = []

with open("paths.txt") as f:
    paths = f.readlines()
    for path in paths:
        row = []
        for attr in path.strip().split(", "):
            row.append(attr.split(":")[1])
        paths_list.append(row)

def find_next_hop(current_sw, dst_sv):
    for path in paths_list:
        if path[0] == current_sw and path[1] == dst_sv:
            return path[2]

with open("full_paths.txt", "w") as f:
    for src_sv_id in range(16):
        for dst_sv_id in range(16):
            if src_sv_id // 4 == dst_sv_id // 4:
                continue

            result_path = [f"sv{src_sv_id+1}"]
            current_sw = f"sw{src_sv_id // 2 + 13}"
            result_path.append(current_sw)

            while True:
                current_sw = find_next_hop(current_sw, f"sv{dst_sv_id + 1}")
                result_path.append(current_sw)
                if current_sw == f"sw{dst_sv_id // 2 + 13}":
                    break

            result_path.append(f"sv{dst_sv_id+1}")
            f.write('->'.join(result_path) + "\n")
