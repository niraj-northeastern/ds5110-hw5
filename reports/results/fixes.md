| problem                                           |   rows | Order (first 8)                          | action                    |
|:--------------------------------------------------|-------:|:-----------------------------------------|:--------------------------|
| Sale Type 'WD ' has a trailing space              |   2536 | [1, 2, 3, 4, 5, 6, 7, 8]                 | strip spaces              |
| MS Zoning: 'C (all)' not in dictionary            |     25 | [214, 305, 306, 307, 308, 721, 727, 728] | change to 'C'             |
| MS Zoning: 'I (all)' not in dictionary            |      2 | [946, 1611]                              | change to 'I'             |
| MS Zoning: 'A (agr)' not in dictionary            |      2 | [1554, 2904]                             | change to 'A'             |
| Neighborhood: 'NAmes' not in dictionary           |    443 | [1, 2, 3, 4, 24, 25, 26, 27]             | change to 'Names'         |
| Bldg Type: '2fmCon' not in dictionary             |     62 | [152, 187, 190, 207, 208, 212, 215, 219] | change to '2FmCon'        |
| Bldg Type: 'Duplex' not in dictionary             |    109 | [84, 126, 136, 139, 159, 206, 217, 218]  | change to 'Duplx'         |
| Bldg Type: 'Twnhs' not in dictionary              |    101 | [30, 31, 32, 34, 35, 36, 51, 98]         | change to 'TwnhsI'        |
| Exterior 2nd: 'CmentBd' not in dictionary         |    126 | [7, 9, 43, 105, 260, 264, 296, 309]      | change to 'CemntBd'       |
| Exterior 2nd: 'Wd Shng' not in dictionary         |     81 | [16, 51, 150, 162, 173, 207, 212, 239]   | change to 'WdShing'       |
| Exterior 2nd: 'Brk Cmn' not in dictionary         |     22 | [34, 35, 36, 410, 411, 412, 413, 414]    | change to 'BrkComm'       |
| Garage Yr Blt is 2207                             |      1 | [2261]                                   | set to NaN                |
| Year Remod/Add before Year Built                  |      1 | [851]                                    | set Year Remod/Add to NaN |
| Mas Vnr Type 'None' but area > 0                  |      7 | [364, 404, 442, 1862, 1914, 2004, 2529]  | set type to NaN           |
| Mas Vnr Type given but area is 0                  |      3 | [1641, 1741, 1786]                       | set area to NaN           |
| Garage Qual says no garage but there is one       |      1 | [1357]                                   | set to NaN                |
| Garage Cond says no garage but there is one       |      1 | [1357]                                   | set to NaN                |
| Bsmt Full Bath empty for a house with no basement |      1 | [1498]                                   | set to 0                  |
| Bsmt Half Bath empty for a house with no basement |      1 | [1498]                                   | set to 0                  |
