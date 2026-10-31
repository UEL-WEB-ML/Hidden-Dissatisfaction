# Rolling-origin fold date ranges

Source: `reports/experiments/p5-s6-e15-content.json`, retained Random Forest development run. The folds are constructed inside the train partition, in chronological order and at order grain.

| Fold | Training rows | Validation rows | Validation start | Validation end |
|---|---:|---:|---|---|
| 1 | 10,681 | 5,308 | 2017-06-01 12:27:11 | 2017-07-18 20:42:29 |
| 2 | 15,989 | 5,365 | 2017-07-18 20:43:22 | 2017-08-24 20:04:21 |
| 3 | 21,354 | 5,354 | 2017-08-24 20:05:52 | 2017-09-30 20:09:53 |

The first fold's training window starts at the earliest train-partition timestamp, 2016-10-11 13:46:32. Fold dates above are suitable for Figure 3.3; the one-second gaps arise from the actual timestamp boundaries between adjacent order records, not an embargo rule.
