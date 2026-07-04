# Session Notes

- Garmin's public/developer APIs do not appear to support consumer bulk edits of Garmin Connect activity gear. This skill uses the unofficial `garminconnect` Python package.
- A real account exposed hiking activities as Garmin type `other`, while activity names contained `Hike` such as `King County Hike`, `Snoqualmie Hike`, and `Newcastle Hike`.
- The working bulk-fix pattern was: select existing gear by name, infer a start date from gear history, fetch broad activity pages, filter locally by activity name, check existing gear per activity, dry-run, then apply after confirmation.
- A successful verification dry run after applying should show every matching activity already has the gear and `Would update: 0`.
