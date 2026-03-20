# EC2 Snapshot Cleaner

Automatically deletes EC2 snapshots older than 1 year using AWS Lambda,
triggered daily by EventBridge, running inside a private VPC.

## Why Terraform?
Terraform is simple, readable, and widely used in the industry. It manages
state so re-runs are safe, and makes it easy to create and destroy all
infrastructure with single commands.

## Architecture
- **EventBridge** triggers the Lambda every day at 2am UTC
- **Lambda** (Python 3.12) runs inside a private VPC subnet
- **IAM Role** gives Lambda permission to describe and delete snapshots
- **VPC Endpoint** allows Lambda to reach AWS EC2 API without needing internet
- **CloudWatch Logs** records every action the Lambda takes

## Prerequisites
- AWS CLI installed and configured (`aws configure`)
- Terraform installed (version 1.5 or higher)
- An AWS account with admin permissions

## How to deploy

### 1. Clone the project
```bash
git clone <your-repo-url>
cd snapshot-cleaner
```

### 2. Initialize Terraform
```bash
terraform init
```

### 3. Preview what will be created
```bash
terraform plan
```

### 4. Deploy everything
```bash
terraform apply
```
Type `yes` when prompted. This creates all infrastructure including
VPC, subnet, IAM role, Lambda, EventBridge rule, and CloudWatch log group.

## How to test the Lambda manually
```bash
aws lambda invoke \
  --function-name ec2-snapshot-cleaner \
  --region us-east-1 \
  --payload '{}' \
  response.json && cat response.json
```

## Dry run mode
The Lambda runs in dry run mode by default (`DRY_RUN=true`).
This means it will log what it would delete without actually deleting anything.
To enable real deletions, change `DRY_RUN` to `false` in `main.tf` under
the Lambda environment variables, then run `terraform apply` again.

## How Lambda runs inside the VPC
The Lambda is configured with a private subnet and security group.
A VPC Interface Endpoint for EC2 allows it to call AWS APIs privately
without needing an internet gateway or NAT gateway.

## Monitoring
- **Logs:** AWS Console → CloudWatch → Log groups → `/aws/lambda/ec2-snapshot-cleaner`
- **Metrics:** AWS Console → CloudWatch → Metrics → Lambda → ec2-snapshot-cleaner
- **To get alerts:** Create a CloudWatch Alarm on `Errors > 0` and connect to SNS email

## Assumptions
- Region: `us-east-1` (can be changed in `variables.tf`)
- Only snapshots owned by this AWS account are checked
- Age threshold is 365 days (configurable via `SNAPSHOT_AGE_DAYS` env var)
- Snapshots in use by AMIs are automatically skipped

## Destroy all resources (cleanup)
```bash
terraform destroy
```
```