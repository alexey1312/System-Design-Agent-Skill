# Design YouTube

Source: Vol. 1 ch. 14 (upstream `14. Youtube`).
Also applies to Netflix, Hulu, and any upload-plus-stream product.

## Scope and numbers

Upload and watch; mobile, web, smart TV; 5 million DAU;
5 videos watched per user per day; 10 % upload one video a day;
average 300 MB; max 1 GB; store on cloud (S3), stream via CDN.
Storage: 5 M × 10 % × 300 MB ≈ 150 TB per day.
CDN cost at CloudFront's $0.02/GB: 5 M × 5 × 0.3 GB × $0.02 ≈ $150,000 per day.

## High-level design

Client, **CDN** (streams videos), **API servers** (everything except streaming:
recommendations, metadata, uploads), **metadata DB** (sharded, replicated),
metadata cache, **original storage** (blob), **transcoding servers**,
**transcoded storage**, **completion queue** and handlers.

### Upload flow

1. Video → original storage.
2. Transcoding servers convert to many formats and resolutions.
3. Transcoded files → transcoded storage → CDN;
   completion events → completion queue → handlers update metadata and notify.

In parallel the client sends metadata (name, size, format) to the API servers.

### Streaming flow

Play from the nearest CDN edge as chunks arrive.
Protocols: MPEG-DASH, Apple HLS, Adobe HDS; each supports different codecs.

## Deep dive: transcoding

Raw video is huge; devices and browsers need different containers and codecs;
adaptive quality follows network conditions.
Container (MP4, AVI) wraps video, audio, metadata; codec (H.264, VP9, HEVC) compresses.

A **DAG** of tasks (inspired by Facebook's streaming video engine):
split into video, audio, metadata; encode video at several resolutions;
generate thumbnails; watermark; merge.

Architecture:

- **Preprocessor**: splits by GOP (group of pictures, a closed set of frames)
  for clients that cannot; generates the DAG from config files;
  stores GOPs and metadata in temporary storage for retries.
- **DAG scheduler**: splits the graph into stages and queues tasks.
- **Resource manager**: task queue (priority), worker queue (utilisation),
  running queue; a scheduler matches tasks to workers.
- **Task workers**: encoders, thumbnailers, watermarkers.
- **Temporary storage**: type chosen per data (cache for metadata, blob for video).
- **Encoded video** output.

## Optimisations

- **Speed**: parallel upload of GOP-aligned chunks (resumable);
  upload centers near users (CDN as ingress);
  message queues between every stage so modules run in parallel.
- **Safety**: pre-signed URLs for uploads; DRM (FairPlay, Widevine, PlayReady),
  AES encryption, visual watermarks.
- **Cost**: serve only popular videos from the CDN, long-tail from origin;
  encode less popular short videos on demand; regional distribution;
  build your own CDN with ISP partnerships (Netflix).

## Error handling

Recoverable (retry a transcoding task, hand off to another worker);
non-recoverable (stop, return an error for a malformed video).

## Wrap-up

Scale the API tier statelessly; shard the metadata DB;
live streaming (latency, smaller chunks, real-time transcoding, DAG must be fast);
takedowns for copyright, pornography, illegal content.
