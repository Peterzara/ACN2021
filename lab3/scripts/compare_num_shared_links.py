from collections import defaultdict

num_ft = defaultdict(int)
with open("num_shared_links_ft.txt") as f:
    for line in f.readlines():
        path, num = line.strip().split(" ")
        num_ft[path] = int(num)

num_sp = defaultdict(int)
with open("num_shared_links_sp.txt") as f:
    for line in f.readlines():
        path, num = line.strip().split(" ")
        num_sp[path] = int(num)

results = defaultdict(list)

for k, v in num_ft.items():
    results[k] = [num_sp[k], v, num_sp[k] - v]

results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1][2])}
with open("num_shared_links.txt", "w") as f:
    f.write("path, sp, ft, diff\n")
    for k, vs in results.items():
        f.write(f"{k}")
        for v in vs:
            f.write(f" {v}")

        f.write("\n")