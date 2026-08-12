# FSroRAutoTrade Changelog

## v3.2.4

- Aligned empty inventory slot selection with FControl's proven implementation.
- Kept the existing 20-second job-item unequip retry and verification flow.

## v3.2.3

- Fixed training-area detection near region boundaries by using the active
  training radius and coordinate distance instead of requiring identical region IDs.
- Kept the three consecutive inside-area checks before automatic trade starts.

## v3.2.2

- Fixed empty inventory slot detection for phBot versions that return empty slots as `{}` instead of `None`.
- Kept the timed inventory refresh and job-item unequip retry behavior introduced in v3.2.1.
