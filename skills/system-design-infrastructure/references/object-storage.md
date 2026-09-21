# S3-like object storage

Source: Vol. 2 ch. 9 (upstream `24. S3-like Object Storage`).

## Storage kinds

| | Block | File | Object |
| --- | --- | --- | --- |
| Mutable content | Yes | Yes | No (versioning instead) |
| Cost | High | Medium–high | Low |
| Performance | High | Medium–high | Low–medium |
| Access | SAS, iSCSI, FC | NFS, SMB | REST |
| Good for | VMs, databases | General file access | Binary and unstructured data, archives |

Object storage: flat namespace of **buckets** holding immutable **objects**
(data plus metadata), optional **versioning**, addressed by URI.
S3 Standard-IA promises eleven nines of durability and 99.9 % availability.

## Scope

Bucket creation, object upload and download, versioning, listing;
objects from tiny to huge; 100 PB per year;
six nines of durability; four nines of availability; storage efficiency.

Estimation: 20 % small (0.5 MB median), 60 % medium (32 MB), 20 % large (200 MB);
a 7200 rpm SATA disk gives 100–150 IOPS;
at 40 % utilisation of 100 PB that is about 0.68 billion objects,
and 1 KB of metadata each is 0.68 TB of metadata.

## Properties that shape the design

Immutable objects; key-value access by URI; write once, read many
(95 % reads); both small and large objects.
Like a UNIX inode, metadata and content are stored separately
so each can scale on its own.

## High-level design

Load balancer → stateless **API service** → **IAM** (auth, authz),
**metadata store** (bucket and object tables), **data store** (bytes by UUID).

- Upload: create bucket (IAM check, metadata row) →
  `PUT /bucket/object` → IAM check → data store returns UUID →
  metadata row with `object_id`, `bucket_id`, name, size, and user metadata.
- Download: `GET /bucket/object` → IAM check →
  metadata lookup by name → fetch bytes by UUID.
  A "folder" is just a name prefix.

## Data store

**Data routing service** (stateless, REST or gRPC): asks the placement service
where to write, writes to and reads from data nodes.
**Placement service**: keeps the virtual cluster map (physical topology),
heart-beats data nodes, and runs as a 5- or 7-node Paxos or Raft group.
**Data nodes**: store bytes, replicate to peers, report disks and usage.

Persistence: routing → primary node → primary replicates to two secondaries →
respond only after replication (consistency over latency);
the replication group is picked deterministically by consistent hashing on the UUID.

### Organising bytes

One file per object wastes 4 KB blocks and exhausts inodes.
Append objects into large files (a few GB) via a WAL;
when full, start a new file.
Serialise writes per file, or pin files to cores to avoid lock contention.
Lookup table per node: `object_id → file, offset, size`,
in a local SQLite (low writes, high reads, no network hop).

### Durability

Replicate across failure domains (rack, data center, network).
With an annual disk failure rate of 0.81 %, three copies reach six nines.
**Erasure coding** (for example 8 + 4 across domains)
costs 50 % overhead instead of 200 %, reaches eleven nines,
but adds computation and read latency (data gathered from many nodes).
Replication for latency-sensitive data; erasure coding for cost and durability.

Checksums per object and per file catch silent corruption;
with erasure coding each chunk is verified separately.

## Metadata store

Tables `bucket` (small; fits one server, scale reads) and `object`.
Shard `object` by `hash(bucket_name, object_name)`:
sharding by bucket alone makes hot shards;
most queries are by name.

Listing by prefix (`WHERE bucket_id = ? AND object_name LIKE 'abc/%'`)
across shards needs scatter-gather and awkward pagination;
accept slow listing or keep a denormalised listing table sharded by bucket.

## Versioning

`object_version` (TIMEUUID) per row; each upload makes a new `object_id`;
deletion inserts a delete marker; reads of a deleted name return 404.

## Multipart upload

Initiate → upload ID → parallel part uploads, each acknowledged with an ETag (MD5) →
complete with the part list → server assembles the object (minutes for large files) →
old parts become garbage.

## Garbage collection

Lazy deletes, orphaned parts, and corrupted data are reclaimed by **compaction**:
copy live objects from a full file into a new one,
update the mapping table transactionally, delete the old file;
run only on files above a size threshold.
