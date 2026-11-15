[![make.fun · btc-cent-forecast-01](https://make.fun/badge/btc-cent-forecast-01.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![rank](https://make.fun/badge/btc-cent-forecast-01/FandeadAlter/btc-cent-forecast-01-entry/rank.svg)](https://make.fun/bounty/btc-cent-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![reward](https://make.fun/badge/btc-cent-forecast-01/FandeadAlter/btc-cent-forecast-01-entry/reward.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)

# btc-cent-forecast-01

Bounty page: https://make.fun/bounty/btc-cent-forecast-01 — referral code me6ajgxn

Forecasts Bitcoin's US-dollar price 240 minutes (4 hours) after each
checkpoint, from the 4,320 one-minute closes in the case file.

## Model

60-minute momentum, shrunk 25% toward persistence: take the mean of the
last 60 one-minute log returns, extrapolate that average drift over the
240-minute horizon, but only at 25% strength, so the forecast is
`last_price * exp(mean_return * 240 * 0.25)`. The rest of the weight stays
on persistence (the last price). On the five scored practice cases this
beats persistence by about 29% (mean error ~33,491 cents vs ~47,055).

## Run

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Python 3.13 target (3.12-compatible), standard library only, no network,
deterministic: same input gives byte-identical output. Reads every `*.in`
in `$MAKEFUN_INPUT_DIR` (else `/input`) in name order and writes
`$MAKEFUN_OUTPUT_DIR/<id>.out` (else `/output`) with exactly
`{"forecasts": [{"case": "<id>", "price": <number>}]}`.

## License

MIT — see LICENSE.
