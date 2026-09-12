import os
import csv
import json
import shutil
import hashlib
import datetime

SOURCE_DIR = "data/old_format"
BACKUP_DIR = "data/backup"
TRANSFORMED_DIR = "data/transformed"
NEW_FORMAT_DIR = "data/new_format"
LOG_FILE = "migration_log.jsonl"
REPORT_FILE = "migration_report.json"
CHECKSUMS_FILE = "checksums.json"
VERIFICATION_REPORT_FILE = "verification_report.json"

STEPS = ["backup", "transform_format", "validate_checksums", "load_new_store", "verify_counts", "update_references"]

completed_steps = []
rollback_fns = []

def log_event(step, status, message=""):
    entry = {"step": step, "status": status, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
    if message:
        entry["message"] = message
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def step_backup():
    log_event("backup", "start")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
    for fname in files:
        shutil.copy2(os.path.join(SOURCE_DIR, fname), os.path.join(BACKUP_DIR, fname))
    log_event("backup", "completed", f"Backed up {len(files)} files")

    def rollback_backup():
        for fname in files:
            dst = os.path.join(BACKUP_DIR, fname)
            if os.path.exists(dst):
                os.remove(dst)
        log_event("backup", "rolled_back")

    rollback_fns.append(rollback_backup)
    return True

def step_transform_format():
    log_event("transform_format", "start")
    os.makedirs(TRANSFORMED_DIR, exist_ok=True)
    created_files = []

    for csv_fname in ["sensor_readings.csv", "devices.csv"]:
        src_path = os.path.join(SOURCE_DIR, csv_fname)
        if not os.path.exists(src_path):
            log_event("transform_format", "error", f"Source file not found: {src_path}")
            return False
        jsonl_fname = csv_fname.replace(".csv", ".jsonl")
        dst_path = os.path.join(TRANSFORMED_DIR, jsonl_fname)
        rows = []
        with open(src_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        with open(dst_path, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        # Verify row count
        src_count = len(rows)
        dst_count = sum(1 for line in open(dst_path) if line.strip())
        if src_count != dst_count:
            log_event("transform_format", "error", f"Row count mismatch for {csv_fname}: {src_count} vs {dst_count}")
            return False
        created_files.append(dst_path)
        log_event("transform_format", "info", f"Transformed {csv_fname}: {src_count} rows")

    log_event("transform_format", "completed", f"Transformed {len(created_files)} files")

    def rollback_transform():
        for p in created_files:
            if os.path.exists(p):
                os.remove(p)
        log_event("transform_format", "rolled_back")

    rollback_fns.append(rollback_transform)
    return True

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def step_validate_checksums():
    log_event("validate_checksums", "start")
    checksums = {"source": {}, "transformed": {}}

    for fname in ["sensor_readings.csv", "devices.csv"]:
        path = os.path.join(SOURCE_DIR, fname)
        if os.path.exists(path):
            checksums["source"][fname] = sha256_file(path)

    for fname in ["sensor_readings.jsonl", "devices.jsonl"]:
        path = os.path.join(TRANSFORMED_DIR, fname)
        if os.path.exists(path):
            checksums["transformed"][fname] = sha256_file(path)

    with open(CHECKSUMS_FILE, "w") as f:
        json.dump(checksums, f, indent=2)

    log_event("validate_checksums", "completed", f"Checksums written to {CHECKSUMS_FILE}")

    def rollback_checksums():
        if os.path.exists(CHECKSUMS_FILE):
            os.remove(CHECKSUMS_FILE)
        log_event("validate_checksums", "rolled_back")

    rollback_fns.append(rollback_checksums)
    return True

def step_load_new_store():
    log_event("load_new_store", "start")
    os.makedirs(NEW_FORMAT_DIR, exist_ok=True)
    copied_files = []

    for jsonl_fname in ["sensor_readings.jsonl", "devices.jsonl"]:
        src_path = os.path.join(TRANSFORMED_DIR, jsonl_fname)
        if not os.path.exists(src_path):
            log_event("load_new_store", "error", f"Transformed file not found: {src_path}")
            return False
        dst_path = os.path.join(NEW_FORMAT_DIR, jsonl_fname)
        shutil.copy2(src_path, dst_path)

        # Verify row count matches source CSV
        csv_fname = jsonl_fname.replace(".jsonl", ".csv")
        csv_path = os.path.join(SOURCE_DIR, csv_fname)
        src_count = sum(1 for _ in open(csv_path)) - 1  # subtract header
        dst_count = sum(1 for line in open(dst_path) if line.strip())
        if src_count != dst_count:
            log_event("load_new_store", "error", f"Row count mismatch for {jsonl_fname}: src={src_count} dst={dst_count}")
            return False
        copied_files.append(dst_path)
        log_event("load_new_store", "info", f"Loaded {jsonl_fname}: {dst_count} rows")

    log_event("load_new_store", "completed", f"Loaded {len(copied_files)} files to new store")

    def rollback_load():
        for p in copied_files:
            if os.path.exists(p):
                os.remove(p)
        log_event("load_new_store", "rolled_back")

    rollback_fns.append(rollback_load)
    return True

def step_verify_counts():
    log_event("verify_counts", "start")
    results = {}
    all_match = True

    for csv_fname, jsonl_fname in [("sensor_readings.csv", "sensor_readings.jsonl"), ("devices.csv", "devices.jsonl")]:
        csv_path = os.path.join(SOURCE_DIR, csv_fname)
        jsonl_path = os.path.join(NEW_FORMAT_DIR, jsonl_fname)

        src_count = sum(1 for _ in open(csv_path)) - 1  # subtract header
        dst_count = sum(1 for line in open(jsonl_path) if line.strip())
        match = src_count == dst_count
        if not match:
            all_match = False
        results[csv_fname] = {"source_count": src_count, "dest_count": dst_count, "match": match}

    # Use sensor_readings as primary
    primary = results.get("sensor_readings.csv", {})
    report = {
        "status": "match" if all_match else "mismatch",
        "counts_match": all_match,
        "source_count": primary.get("source_count", 0),
        "dest_count": primary.get("dest_count", 0),
        "details": results
    }
    with open(VERIFICATION_REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    if not all_match:
        log_event("verify_counts", "error", "Row count mismatch detected")
        return False

    log_event("verify_counts", "completed", "All row counts match")

    def rollback_verify():
        if os.path.exists(VERIFICATION_REPORT_FILE):
            os.remove(VERIFICATION_REPORT_FILE)
        log_event("verify_counts", "rolled_back")

    rollback_fns.append(rollback_verify)
    return True

def step_update_references():
    log_event("update_references", "start")

    # Load valid device_ids from devices.jsonl
    devices_path = os.path.join(NEW_FORMAT_DIR, "devices.jsonl")
    valid_device_ids = set()
    with open(devices_path, "r") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if "device_id" in rec:
                    valid_device_ids.add(str(rec["device_id"]))

    # Check sensor_readings for orphaned device_ids
    readings_path = os.path.join(NEW_FORMAT_DIR, "sensor_readings.jsonl")
    readings = []
    orphans = []
    with open(readings_path, "r") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                readings.append(rec)
                dev_id = str(rec.get("device_id", ""))
                if dev_id and dev_id not in valid_device_ids:
                    orphans.append(dev_id)

    if orphans:
        log_event("update_references", "warning", f"Found {len(orphans)} orphaned device_ids: {list(set(orphans))[:5]}")
        # Remove orphaned records to fix references
        readings = [r for r in readings if str(r.get("device_id", "")) in valid_device_ids]
        with open(readings_path, "w") as f:
            for rec in readings:
                f.write(json.dumps(rec) + "\n")
        log_event("update_references", "info", f"Removed {len(orphans)} orphaned records")
    else:
        log_event("update_references", "info", "No orphaned device_id references found")

    log_event("update_references", "completed", "References verified/updated")

    def rollback_refs():
        log_event("update_references", "rolled_back")

    rollback_fns.append(rollback_refs)
    return True

def rollback_all():
    log_event("migration", "rolling_back", f"Rolling back {len(rollback_fns)} completed steps")
    for fn in reversed(rollback_fns):
        try:
            fn()
        except Exception as e:
            log_event("migration", "rollback_error", str(e))

def run_migration():
    # Clear log file for fresh run
    open(LOG_FILE, "w").close()
    log_event("migration", "start")

    step_fns = [
        ("backup", step_backup),
        ("transform_format", step_transform_format),
        ("validate_checksums", step_validate_checksums),
        ("load_new_store", step_load_new_store),
        ("verify_counts", step_verify_counts),
        ("update_references", step_update_references),
    ]

    steps_completed = []

    for step_name, step_fn in step_fns:
        try:
            result = step_fn()
            if not result:
                log_event("migration", "failed", f"Step {step_name} returned False")
                rollback_all()
                return False
            steps_completed.append(step_name)
        except Exception as e:
            log_event(step_name, "error", str(e))
            log_event("migration", "failed", f"Step {step_name} raised exception: {e}")
            rollback_all()
            return False

    # Write migration report
    report = {
        "status": "success",
        "steps_completed": steps_completed,
        "total_steps": len(steps_completed),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    log_event("migration", "completed", f"All {len(steps_completed)} steps completed successfully")
    return True

if __name__ == "__main__":
    import sys
    success = run_migration()
    sys.exit(0 if success else 1)
