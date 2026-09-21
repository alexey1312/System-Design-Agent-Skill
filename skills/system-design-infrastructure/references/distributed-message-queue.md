# Distributed message queue

Source: Vol. 2 ch. 4 (upstream `19. Distributed Message Queue`).
The design converges on a Kafka-style log rather than a traditional queue.

## Why a queue

Decoupling, independent scaling of producers and consumers,
availability when one side is down, and producers that never wait.
Kafka and Pulsar are event-streaming platforms rather than queues,
but the features have converged.

## Scope

- Text messages of a few KB.
- Messages can be consumed repeatedly by different consumers (not traditional).
- Order preserved (not traditional).
- Retention of two weeks; historical data can be truncated.
- Delivery semantics configurable: at-most-once, at-least-once, exactly-once.
- High throughput for log aggregation and low latency for classic use, by configuration.
- Persistent, replicated, and able to absorb sudden surges.

## Model

- **Point-to-point**: one consumer gets each message; consumed messages disappear.
- **Publish-subscribe**: messages belong to a topic; every subscriber gets them.
- **Partitions** shard a topic; **brokers** host partitions;
  order holds within a partition; a message's position is its **offset**.
  A partition key (for example `user_id`) pins related messages to one partition.
- **Consumer groups** share the work; each group tracks its own offsets;
  one consumer per partition inside a group keeps ordering,
  so a group cannot have more active consumers than partitions.

Components: clients, brokers, data storage (partitions on disk),
state storage (consumer offsets), metadata storage (topic config),
and a coordination service (ZooKeeper) for membership and leader election.

## Deep dive

### Storage: write-ahead log

Access is write-heavy and read-heavy, append-only, sequential.
Databases fit poorly.
A WAL of segments per partition fits:
only the newest segment takes writes, old segments are read-only,
and sequential HDD access reaches hundreds of MB/s with the OS page cache doing the rest.

### Message layout

Key (chooses the partition: `hash(key) % partitions`, producer may override),
value, topic, partition, offset, timestamp, size, CRC.
Keys need not be unique.
The same schema end to end avoids copying.

### Batching everywhere

Producer, broker and consumer batch;
it amortises round trips and turns writes into large sequential appends.
Bigger batches mean more throughput and more latency;
tune down for queue-like latency, or add partitions to recover throughput.

### Producer flow

A separate routing layer adds a hop and prevents batching,
so the routing logic moves into the producer client with a buffer:
the producer reads the replica plan from metadata,
sends a batch to the partition leader,
followers pull, and the leader acknowledges after enough replicas caught up.

### Consumer flow: pull

Push gives low latency but overwhelms slow consumers.
Pull lets the consumer set the pace, suits batch processing,
and long polling hides the empty-poll cost.
Joining a group: hash the group name to find its coordinator broker,
receive a partition assignment, fetch from the last committed offset,
process, commit.
The order of *process* and *commit* decides the delivery semantics.

### Rebalancing

Triggered when a consumer joins, leaves, or stops heart-beating.
The coordinator asks all members to rejoin,
elects a group leader that computes the partition plan,
and broadcasts it.

### State and metadata

Consumer offsets: frequent small consistent reads and writes → ZooKeeper.
Topic configuration: small, rarely changed, must be consistent → ZooKeeper.
ZooKeeper also elects broker leaders, so brokers keep only message data.

### Replication and ISR

Each partition has one leader and several followers on other brokers.
The **in-sync replica** set contains followers within `replica.lag.max.messages` of the leader;
a message is committed once every ISR member has it.

| ACK | Wait for | Trade-off |
| --- | --- | --- |
| `all` | Every ISR member | Slowest, most durable |
| `1` | Leader only | Fast, may lose data on leader crash |
| `0` | Nobody | Fastest, fire-and-forget |

Consumers read from the leader (simple; connection count is low);
a follower may serve a consumer in another data center.

### Scaling

Producers: add instances.
Consumers: add groups, or consumers within a group (rebalance).
Brokers: on failure a new leader is elected and partitions redistributed;
spread replicas across brokers and racks; mirror across data centers if needed;
a new broker temporarily over-replicates until it catches up.
Partitions: adding one notifies producers and triggers rebalancing;
removing one keeps it readable until retention expires, then rebalances.

### Delivery semantics

- **At-most-once**: producer does not retry; consumer commits before processing.
- **At-least-once**: producer retries with `ACK=1` or `all`;
  consumer commits after processing; duplicates possible, so consumers dedupe.
- **Exactly-once**: costly; needs idempotent producers and transactional offset commits.

### Advanced features

Filtering by message tags in the broker (not by payload, which may be encrypted).
Delayed and scheduled messages via a holding topic and a timing wheel.

## Wrap-up

Protocols (AMQP, Kafka wire protocol), retry topics, archiving to HDFS or S3.
