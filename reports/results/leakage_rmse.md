|                                           |   CV RMSE (log $) |   fold sd |
|:------------------------------------------|------------------:|----------:|
| A (SalePrice-quintile median, full table) |           0.16243 |   0.01369 |
| B (KNN fit on full table, then CV)        |           0.16231 |   0.01345 |
| C (KNN inside Pipeline)                   |           0.16231 |   0.01341 |
| reference: Lot Frontage dropped           |           0.16258 |   0.01248 |
