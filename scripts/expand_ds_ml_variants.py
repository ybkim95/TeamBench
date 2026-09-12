#!/usr/bin/env python3
"""Expand DS/ML tasks into seed variants and verify each grader."""
import sys, os, json, tempfile, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def expand_domain(domain_path):
    sys.path.insert(0, domain_path)
    # Clear cached modules
    for k in list(sys.modules.keys()):
        if k.startswith('generators'):
            del sys.modules[k]

    from generators.registry import get_generator

    tasks_dir = os.path.join(domain_path, "tasks")
    base_tasks = sorted([d for d in os.listdir(tasks_dir) if os.path.isdir(os.path.join(tasks_dir, d)) and not "_s" in d])

    created = 0
    verified = 0
    failed = 0

    for tid in base_tasks:
        try:
            gen = get_generator(tid)
        except Exception as e:
            print(f"  {tid}: generator error - {e}")
            continue

        seen = set()
        for seed in range(10):
            try:
                r = gen.generate(seed=seed)
                content_hash = hash(str(sorted([(k, v[:100]) for k, v in r.workspace_files.items()])))
                if content_hash in seen:
                    continue
                seen.add(content_hash)

                if seed == 0:
                    # Base task already exists, just verify it
                    pass
                else:
                    # Create variant
                    instance_id = f"{tid}_s{seed}"
                    instance_dir = os.path.join(tasks_dir, instance_id)
                    if os.path.isdir(instance_dir):
                        continue

                    os.makedirs(instance_dir, exist_ok=True)
                    src_dir = os.path.join(tasks_dir, tid)
                    for f in ["task.yaml", "grade.sh"]:
                        src_f = os.path.join(src_dir, f)
                        if os.path.isfile(src_f):
                            shutil.copy2(src_f, os.path.join(instance_dir, f))

                    with open(os.path.join(instance_dir, "spec.md"), "w") as f:
                        f.write(r.spec_md)
                    with open(os.path.join(instance_dir, "brief.md"), "w") as f:
                        f.write(r.brief_md)

                # Verify grader on this seed
                tmpdir = tempfile.mkdtemp()
                ws = os.path.join(tmpdir, "workspace")
                rp = os.path.join(tmpdir, "reports")
                os.makedirs(ws)
                os.makedirs(rp)
                gen.write_to_disk(r, ws, rp)

                src_dir = os.path.join(tasks_dir, tid)
                grader = os.path.abspath(os.path.join(src_dir, "grade.sh"))

                res = subprocess.run(
                    ["bash", grader, ws, rp, os.path.join(tmpdir, "sub"), os.path.abspath(src_dir)],
                    capture_output=True, text=True, timeout=60, cwd=ws
                )

                sf = os.path.join(rp, "score.json")
                if os.path.isfile(sf):
                    s = json.load(open(sf))
                    p = s.get("secondary", {}).get("partial_score", 1.0)
                    if not s.get("pass") and p < 1.0:
                        verified += 1
                        if seed > 0:
                            created += 1
                    else:
                        # Bad — remove variant if we created it
                        if seed > 0:
                            instance_dir = os.path.join(tasks_dir, f"{tid}_s{seed}")
                            if os.path.isdir(instance_dir):
                                shutil.rmtree(instance_dir)
                        failed += 1
                else:
                    if seed > 0:
                        instance_dir = os.path.join(tasks_dir, f"{tid}_s{seed}")
                        if os.path.isdir(instance_dir):
                            shutil.rmtree(instance_dir)
                    failed += 1

                shutil.rmtree(tmpdir)

            except Exception as e:
                failed += 1

    sys.path.remove(domain_path)
    return created, verified, failed


if __name__ == "__main__":
    for name, path in [("DS", os.path.join(REPO, "teambench-ds")),
                        ("ML", os.path.join(REPO, "teambench-ml"))]:
        print(f"\n=== TeamBench-{name} ===")
        created, verified, failed = expand_domain(path)
        total = len([d for d in os.listdir(os.path.join(path, "tasks")) if os.path.isdir(os.path.join(path, "tasks", d))])
        print(f"  Created: {created} new variants")
        print(f"  Verified: {verified} (grader discriminates)")
        print(f"  Failed: {failed}")
        print(f"  Total tasks: {total}")
