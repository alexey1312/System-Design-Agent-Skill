# Sources

Every reference in these skills condenses one chapter of
*System Design Interview – An Insider's Guide* (Alex Xu, Volume 1)
or *System Design Interview – An Insider's Guide: Volume 2* (Alex Xu, Sahn Lam),
as summarised in the community notes at
<https://github.com/liquidslr/system-design-notes>.
The notes carry no licence file,
so the references here are rewritten in the skills' own words,
without the book figures.
Nothing in `references/` is a quotation.

## How to cite

Cite the volume and chapter whenever a recommendation rests on the books,
and name the section when it helps the reader find the passage:

> Fan out on write for most users and on read for celebrities
> (Vol. 1 ch. 11 › Fanout service).

Anything that does not come from a chapter is *inference*.
Say so, and say what it rests on:
a number the user gave, a well-known production system, or general practice.
The books were written in 2020 (Vol. 1) and 2022 (Vol. 2);
vendor names and prices in them may be dated.
Say that when a decision hinges on one.

## Chapter map

| Chapter | Title | Skill | Reference |
| --- | --- | --- | --- |
| Vol. 1 ch. 1 | Scale from zero to millions of users | `system-design-interview` | `references/building-blocks.md` |
| Vol. 1 ch. 2 | Back-of-the-envelope estimation | `system-design-interview` | `references/estimation-cheatsheet.md` |
| Vol. 1 ch. 3 | A framework for system design interviews | `system-design-interview` | `references/framework.md` |
| Vol. 1 ch. 4 | Design a rate limiter | `system-design-infrastructure` | `references/rate-limiter.md` |
| Vol. 1 ch. 5 | Design consistent hashing | `system-design-infrastructure` | `references/consistent-hashing.md` |
| Vol. 1 ch. 6 | Design a key-value store | `system-design-infrastructure` | `references/key-value-store.md` |
| Vol. 1 ch. 7 | Design a unique ID generator in distributed systems | `system-design-infrastructure` | `references/unique-id-generator.md` |
| Vol. 1 ch. 8 | Design a URL shortener | `system-design-content-platforms` | `references/url-shortener.md` |
| Vol. 1 ch. 9 | Design a web crawler | `system-design-content-platforms` | `references/web-crawler.md` |
| Vol. 1 ch. 10 | Design a notification system | `system-design-realtime-messaging` | `references/notification-system.md` |
| Vol. 1 ch. 11 | Design a news feed system | `system-design-content-platforms` | `references/news-feed.md` |
| Vol. 1 ch. 12 | Design a chat system | `system-design-realtime-messaging` | `references/chat-system.md` |
| Vol. 1 ch. 13 | Design a search autocomplete system | `system-design-content-platforms` | `references/search-autocomplete.md` |
| Vol. 1 ch. 14 | Design YouTube | `system-design-content-platforms` | `references/video-streaming.md` |
| Vol. 1 ch. 15 | Design Google Drive | `system-design-content-platforms` | `references/cloud-file-storage.md` |
| Vol. 2 ch. 1 | Proximity service | `system-design-geospatial` | `references/proximity-service.md` |
| Vol. 2 ch. 2 | Nearby friends | `system-design-geospatial` | `references/nearby-friends.md` |
| Vol. 2 ch. 3 | Google Maps | `system-design-geospatial` | `references/maps-navigation.md` |
| Vol. 2 ch. 4 | Distributed message queue | `system-design-infrastructure` | `references/distributed-message-queue.md` |
| Vol. 2 ch. 5 | Metrics monitoring and alerting system | `system-design-infrastructure` | `references/metrics-monitoring.md` |
| Vol. 2 ch. 6 | Ad click event aggregation | `system-design-realtime-messaging` | `references/ad-click-aggregation.md` |
| Vol. 2 ch. 7 | Hotel reservation system | `system-design-transactions` | `references/hotel-reservation.md` |
| Vol. 2 ch. 8 | Distributed email service | `system-design-realtime-messaging` | `references/email-service.md` |
| Vol. 2 ch. 9 | S3-like object storage | `system-design-infrastructure` | `references/object-storage.md` |
| Vol. 2 ch. 10 | Real-time gaming leaderboard | `system-design-realtime-messaging` | `references/gaming-leaderboard.md` |
| Vol. 2 ch. 11 | Payment system | `system-design-transactions` | `references/payment-system.md` |
| Vol. 2 ch. 12 | Digital wallet | `system-design-transactions` | `references/digital-wallet.md` |
| Vol. 2 ch. 13 | Stock exchange | `system-design-transactions` | `references/stock-exchange.md` |

The upstream notes number the chapters 1–28 straight through
(Vol. 2 ch. 1 is their `16. Proximity Service`).
Both numberings are accepted in a citation;
the table above is the mapping.

## Further reading the notes point to

The upstream README lists papers and engineering posts per topic.
The ones worth naming in an answer:

- Rate limiting: Martin Fowler's *Circuit Breaker*; Uber's `ratelimit` Go package (leaky bucket).
- Consistent hashing: Tom White's *Consistent Hashing*; Stanford CS168 lecture 1; the Cassandra paper; Discord's *Scaling Elixir*; Google Maglev.
- Key-value store: the Amazon Dynamo paper; Cassandra architecture docs; the Bigtable paper.
- Unique IDs: Flickr ticket servers; Twitter Snowflake.
- Web crawler: Olston and Najork's crawling survey; Google's dynamic rendering guide.
- Chat: *How Discord stores billions of messages*; Slack's Flannel edge cache.
- Autocomplete: Prefixy; the Prefix Hash Tree paper.
- Video: YouTube architecture on High Scalability; Netflix's per-shot encoding posts.
- File sync: Neil Fraser's *Differential Synchronization*.
