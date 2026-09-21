# Design Google Drive

Source: Vol. 1 ch. 15 (upstream `15. Google Drive`).
Dropbox and OneDrive follow the same shape.

## Scope and numbers

Upload and download; sync across devices; revision history;
sharing; notifications on edit, delete, share.
Reliability (no data loss), fast sync, low bandwidth, scalable, highly available.
50 million signed up, 10 million DAU; 10 GB free each;
2 uploads a day, 500 KB average; 10 GB max file.
Total capacity 50 M × 10 GB = 500 PB; upload QPS 10 M × 2 ÷ 86,400 ≈ 240, peak 480.

## APIs

- Upload: simple for small files; **resumable** for large or flaky
  (`?uploadType=resumable`: get a resumable URL, upload chunks, resume after interruption).
- Download: `GET /files/download` with the path.
- Revisions: `GET /files/list_revisions` with path and limit.
All over HTTPS with authentication.

## From one server to many

A single server with `drive/<namespace>/<path>` on local disk, an API, and a metadata DB
fills its disk.
Shard by `user_id`, then move files to S3 (durable, cross-region replication),
add a load balancer, more web servers, metadata replication and sharding.

**Sync conflicts**: the first version processed wins; the loser gets both versions
and merges or overrides.

## Improved design

Block servers, cloud storage, cold storage, load balancer, API servers,
metadata DB and cache, **notification service** (pub/sub), **offline backup queue**.

- **Block servers** split files into blocks (4 MB max), hash each,
  compress and encrypt, and store them; a file is its block list in order.
  Only changed blocks travel (**delta sync**).
- **Metadata DB** (relational for ACID): `user`, `device`, `namespace`,
  `file`, `file_version`, `block`, sharded and replicated.

### Upload flow

1. Client → block servers → blocks to cloud storage (compressed, encrypted).
2. Client → API servers → metadata `pending` → storage callback → `uploaded` →
   notification service tells other devices.

### Download flow

Triggered by a notification (online) or by pulling on reconnect (offline);
fetch metadata, then the changed blocks, rebuild the file.

### Notification service

Long polling (Dropbox's choice): communication is one-way and infrequent,
so WebSocket's duplex connection is unnecessary.

## Storage savings

Deduplicate blocks by hash at the account level;
cap the number of revisions and keep only valuable ones;
cold storage (S3 Glacier) for months-old files.

## Failure handling

Load balancer failover; block-server work picked up by others;
metadata primary failover and replica replacement; cross-region restores;
notification server loss (Dropbox handles over a million connections per box)
means clients reconnect elsewhere slowly; offline queue is replicated.

## Wrap-up

Uploading directly to cloud storage (faster, but chunking, encryption
and compression move into every client platform);
presence service split from notifications.
