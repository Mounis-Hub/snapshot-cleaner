import boto3
import logging
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    region      = os.environ.get("AWS_REGION_NAME", "us-east-1")
    age_days    = int(os.environ.get("SNAPSHOT_AGE_DAYS", "365"))
    dry_run     = os.environ.get("DRY_RUN", "false").lower() == "true"

    ec2 = boto3.client("ec2", region_name=region)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=age_days)

    logger.info(f"Starting cleanup | cutoff={cutoff_date.date()} | dry_run={dry_run}")

    try:
        paginator = ec2.get_paginator("describe_snapshots")
        pages = paginator.paginate(OwnerIds=["self"])
    except Exception as e:
        logger.error(f"Failed to describe snapshots: {e}")
        raise

    deleted_count = 0
    skipped_count = 0
    error_count   = 0

    for page in pages:
        for snapshot in page["Snapshots"]:
            snapshot_id = snapshot["SnapshotId"]
            start_time  = snapshot["StartTime"]

            if start_time >= cutoff_date:
                skipped_count += 1
                continue

            logger.info(f"{'[DRY RUN] Would delete' if dry_run else 'Deleting'} snapshot: {snapshot_id} | created={start_time.date()}")

            if not dry_run:
                try:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    deleted_count += 1
                    logger.info(f"Successfully deleted: {snapshot_id}")
                except Exception as e:
                    logger.error(f"Error deleting {snapshot_id}: {e}")
                    error_count += 1
            else:
                deleted_count += 1

    summary = {"deleted": deleted_count, "skipped": skipped_count, "errors": error_count}
    logger.info(f"Done: {summary}")
    return summary