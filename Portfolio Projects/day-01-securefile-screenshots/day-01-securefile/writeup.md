# Day 01 — SecureFile: Document Ingestion Pipeline

## Business Problem
An insurance company receives thousands of claim documents daily via email. 
Agents manually download and upload files to a shared drive with no audit 
trail, no automation, and recurring compliance failures. The goal was to 
replace this process with a serverless, automated pipeline that provides 
a complete audit trail and real-time notifications.

## Architecture
![SecureFile Architecture](./diagram.png)

## Services Used
| Service | Purpose |
|---------|---------|
| S3 | Document storage — versioned, encrypted, private |
| Lambda | Event-driven processing on upload |
| DynamoDB | Audit log — every upload permanently recorded |
| SNS | Ops notification on file arrival |
| CloudWatch | Lambda error alerting |
| IAM | Least-privilege execution role |

## Architecture Decisions

**S3 over shared drive or EFS** — Object storage designed for this use case. 
Serverless, scales infinitely, natively triggers Lambda on upload. Block and 
file storage require persistent compute running around the clock. Versioning 
enabled to satisfy the compliance requirement — every version of every document 
preserved permanently.

**Lambda over EC2** — The workload is event-driven. Something only needs to 
happen when a file arrives. Lambda wakes up on upload, runs for 2-3 seconds, 
and shuts down. EC2 would sit idle 99% of the time at continuous hourly cost 
with no benefit.

**DynamoDB over RDS** — The audit log is simple key-value data with no 
relational requirements. Each record is a flat document — file ID, filename, 
bucket, size, timestamp. DynamoDB is serverless, always free at this scale, 
and writes in milliseconds. RDS would require a running instance, cost money 
around the clock, and add complexity without any benefit for this data model.

**SNS for notifications** — SNS decouples the notification logic from the 
processing logic. Lambda publishes one message to the topic and walks away. 
SNS handles delivery to every subscriber. Adding a new notification channel 
— a second email, SMS, Slack — requires no code changes, just a new 
subscription.

**SSE-S3 encryption** — Satisfies the encryption at rest requirement at zero 
cost. AWS manages the keys automatically. In a production HIPAA environment 
this would be SSE-KMS to get a CloudTrail audit trail on every encryption 
and decryption event.

**On-demand DynamoDB capacity** — Upload patterns are sporadic and 
unpredictable. On-demand capacity charges per request only when uploads 
happen. Provisioned capacity would charge for reserved throughput around 
the clock whether files are being uploaded or not.

**Least-privilege IAM policy** — Lambda's execution role grants only what 
the function actually needs: GetObject on the specific bucket, PutItem on 
the specific table, Publish to the specific topic, and CloudWatch log writes. 
No broad managed policies. Each permission scoped to a specific resource ARN.

## Test Results
- Uploaded evan-akerly-resume.pdf to S3 bucket
- Lambda triggered automatically via S3 PUT event
- DynamoDB audit record created with UUID file_id and timestamp
- SNS email delivered to KU inbox within seconds
- CloudWatch logs confirmed successful execution in 520ms
- CloudWatch alarm configured to fire on any Lambda error

## Note on Process
These projects were built with AI assistance while actively learning cloud 
engineering. The focus was not on writing code from memory but on understanding 
the reasoning behind every architecture decision — why S3 over EFS, why Lambda 
over EC2, why DynamoDB over RDS, why least-privilege IAM. The goal is to 
progressively reduce reliance on AI assistance as the decision-making framework 
becomes internalized. By Day 16 architecture decisions will be made independently 
before building.
