# Design a notification system

Source: Vol. 1 ch. 10 (upstream `10. Notification System`).

## Scope

Push (iOS, Android, desktop), SMS, email; soft real-time;
triggered by client apps or server schedules;
10 million push, 1 million SMS, 5 million emails a day;
users can opt out per channel.

## Channels and providers

| Channel | Provider | Needs |
| --- | --- | --- |
| iOS push | APNS | Device token, payload |
| Android push | FCM | Device token |
| SMS | Twilio, Nexmo | Phone number |
| Email | SendGrid, Mailchimp | Address |

Contact info is collected at install or sign-up:
device tokens in a table (a user has many devices),
phone and email in the user table.

## First design and its flaws

Services (billing reminders, shipping updates) → one notification server →
third parties.
A single server is a single point of failure, hard to scale,
and a bottleneck when volume spikes.

## Improved design

- Several stateless **notification servers** with APIs, validation,
  and cache/DB lookups to render messages.
- Database and cache outside the servers.
- One **message queue per channel** as buffer.
- **Workers** pull events and call the provider.

Flow: trigger → notification servers → queue → workers → provider → device.

## Deep dive

- **Reliability**: persist each notification in a log database before sending;
  retry on provider failure; alert on repeated failures.
- **Deduplication**: check the event ID before sending; discard repeats.
  At-least-once delivery means an occasional duplicate anyway.
- **Templates** for consistent, fast-to-author messages.
- **Settings** table: `user_id, channel, opt_in`; check before sending.
- **Rate limiting** per user, so people are not flooded and do not opt out.
- **Retry** with a queue; exponential backoff.
- **Security**: `appKey` and `appSecret` for push APIs.
- **Monitoring**: queue depth drives worker scaling.
- **Event tracking**: open rate, click rate, engagement, via an analytics service.

Final flow: trigger → server (auth, validate, rate limit) → queue →
worker (dedupe, settings, retry, log) → provider.
