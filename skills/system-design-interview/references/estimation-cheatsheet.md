# Back-of-the-envelope estimation

Condensed from Vol. 1 ch. 2.
Estimates exist to check that a design can carry the load,
not to be precise.
Round aggressively, write every assumption down, and label every unit.
Run `scripts/estimate.py` for the arithmetic;
it prints the assumptions next to the results so they can be challenged.

## Powers of two

| Power | Exact | Approximate | Name |
| --- | --- | --- | --- |
| 2^10 | 1,024 | 1 thousand | 1 KB |
| 2^20 | 1,048,576 | 1 million | 1 MB |
| 2^30 | 1,073,741,824 | 1 billion | 1 GB |
| 2^40 | 1.1 × 10^12 | 1 trillion | 1 TB |
| 2^50 | 1.1 × 10^15 | 1 quadrillion | 1 PB |

In an interview, treat 1 KB as 1,000 bytes and 1 MB as 10^6 bytes.
The 2.4 % error does not matter at the precision estimates need.
`estimate.py` uses decimal units for storage and says so in its output.

## Latency numbers every programmer should know

| Operation | Time | Rule of thumb |
| --- | --- | --- |
| L1 cache reference | 0.5 ns | |
| Branch mispredict | 5 ns | |
| L2 cache reference | 7 ns | 14× L1 |
| Mutex lock/unlock | 25 ns | |
| Main memory reference | 100 ns | 20× L2, 200× L1 |
| Compress 1 KB with Zippy | 10 µs | |
| Send 2 KB over 1 Gbps network | 20 µs | |
| Read 1 MB sequentially from memory | 250 µs | |
| Round trip within the same data center | 500 µs | |
| Read 1 MB sequentially from SSD | 1 ms | 4× memory |
| Disk seek | 10 ms | 20× a data-center round trip |
| Read 1 MB sequentially from disk | 30 ms | 120× memory |
| Send a packet CA → Netherlands → CA | 150 ms | |

What to take from the table:

- Memory is fast, disk is slow.
  Avoid disk seeks; prefer sequential access.
- Simple compression is cheap.
  Compress before sending anything across the internet.
- Data centers are usually in different regions,
  and a cross-region round trip costs as much as 300 disk-free memory reads.

## Availability numbers

| Availability | Downtime per day | Downtime per year |
| --- | --- | --- |
| 99 % | 14.4 min | 3.65 days |
| 99.9 % | 1.44 min | 8.77 hours |
| 99.99 % | 8.64 s | 52.6 min |
| 99.999 % | 864 ms | 5.26 min |
| 99.9999 % | 86.4 ms | 31.6 s |

Cloud providers publish SLAs of 99.9 % or better.
`scripts/estimate.py availability 99.99` prints the row for any figure.

## Worked example: Twitter QPS and storage

Assumptions:

- 300 million monthly active users, 50 % of them daily → 150 million DAU.
- 2 tweets per user per day; 10 % carry media.
- Retain data for 5 years.

Results:

- Tweet QPS = 150 M × 2 ÷ 86,400 s ≈ 3,500. Peak ≈ 2× ≈ 7,000.
- Tweet size: `tweet_id` 64 B, text 140 B, media 1 MB.
- Media storage per day = 150 M × 2 × 10 % × 1 MB = 30 TB.
- Five-year media storage ≈ 30 TB × 365 × 5 ≈ 55 PB.

```bash
python3 scripts/estimate.py traffic --dau 150M --actions-per-day 2 \
  --payload 204B --media-share 0.1 --media-size 1MB --retention 5y
```

## Shortcuts

- A day is 86,400 s. Use 10^5 s to make QPS mental arithmetic easy:
  1 million events per day ≈ 10 QPS; 100 million per day ≈ 1,000 QPS.
- Peak factor: 2× is the book default; use 5× for bursty traffic (ads, trading, launches).
- Read/write ratio: state it. 10:1 is a common default for content systems.
- Cache sizing (the 80/20 rule): cache 20 % of a day's read volume.
- Storage growth: daily volume × 365 × years of retention; add replication factor when sizing disks.
- One relational database node handles on the order of 1,000 TPS of transactional writes
  before it needs sharding (Vol. 2 ch. 12 uses this figure).
- One HDD delivers 100–150 random IOPS (Vol. 2 ch. 9);
  sequential writes are far faster than the number suggests.

## Common estimation targets

| Target | How |
| --- | --- |
| QPS and peak QPS | daily events ÷ 86,400, × peak factor |
| Storage | events per day × size × retention, × replication |
| Bandwidth | ingress = storage per day ÷ 86,400; egress = read QPS × object size |
| Cache | 20 % of daily reads × object size |
| Servers | peak QPS ÷ QPS one server sustains |
