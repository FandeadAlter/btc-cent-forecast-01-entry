#!/usr/bin/env python3
"""Forecast Bitcoin's price 4 hours ahead, one case per input file.

Model (see DESIGN.md): 60-minute momentum, shrunk 25% toward persistence.

The last hour's average one-minute log drift is extrapolated over the
240-minute horizon, but only at a quarter of its full strength, so most of
the weight stays on the checkpoint close itself:

    forecast = last_price * exp(mean(last 60 log returns) * 240 * 0.25)

On the five scored practice cases this scores a mean error of about
33,491 cents, roughly 29% below the persistence baseline (47,055 cents).

The program is deliberately boring: Python 3.13 target (3.12-compatible),
standard library only, no network, no randomness, no wall-clock. The same
input therefore always produces byte-identical output.

Usage:
    MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py

It reads every ``*.in`` file in the input directory, in name order, and
writes one ``<id>.out`` per file containing exactly::

    {"forecasts": [{"case": "<id>", "price": <number>}]}

with the price rounded to 5 decimals and clamped into (0, 10,000,000).
"""

import json
import math
import os

# --- Model parameters -------------------------------------------------------

#: How many of the most recent one-minute log returns feed the drift.
WINDOW_MINUTES = 60
#: Fraction of the extrapolated drift to keep; the rest stays on persistence.
SHRINK_FACTOR = 0.25
#: Forecast horizon, in minutes (4 hours).
HORIZON_MINUTES = 240

# --- Output grid ------------------------------------------------------------

#: Smallest positive price on the grid: one unit of its 5 decimals.
MIN_PRICE = 0.00001
#: Largest grid price below the scorer's exclusive 10,000,000 cap.
MAX_PRICE = 9_999_999.99999
#: Decimals of a dollar the price grid (and the output) carries.
PRICE_DECIMALS = 5

#: Fallback guess when a case carries no usable price at all. Any finite
#: positive number keeps the case valid; this value is never expected to
#: occur on a real case, which always holds 4,320 closes.
FALLBACK_PRICE = 1.0


def resolve_directories():
    """Return the (input, output) directories for this run.

    The grader's container leaves both environment variables unset, in
    which case the conventional ``/input`` and ``/output`` apply.
    """
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    return input_dir, output_dir


def list_case_files(input_dir):
    """Return the case filenames in the input directory, in name order.

    Sorting by name (not by directory order) is part of determinism: two
    runs over the same inputs must visit the cases in the same order.
    """
    return sorted(name for name in os.listdir(input_dir) if name.endswith(".in"))


def load_case(path):
    """Load one case file, returning ``(case_id, raw_prices)``.

    ``case_id`` comes from the file's own ``case`` field when present and
    falls back to the filename stem. A file that cannot be parsed at all
    yields no prices, and the caller falls back to a valid placeholder
    forecast rather than leaving the case without an output.
    """
    stem = os.path.basename(path)[:-3]  # strip the ".in" suffix
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        case_id = data.get("case", stem)
        raw_prices = data["markets"][0]["prices"]
    except Exception:
        return stem, []
    return case_id, raw_prices


def usable_closes(raw_prices):
    """Keep only the prices a log return can be computed from.

    A return needs two positive, finite closes, so non-numbers, NaN,
    infinities, zeros and negatives are dropped here, before any
    arithmetic. The order of the surviving closes is preserved.
    """
    return [
        price
        for price in raw_prices
        if isinstance(price, (int, float)) and math.isfinite(price) and price > 0
    ]


def log_returns(closes):
    """Return the one-minute log returns ``ln(p[i+1] / p[i])``."""
    return [
        math.log(closes[i + 1] / closes[i]) for i in range(len(closes) - 1)
    ]


def recent_drift(returns):
    """Mean of the most recent log returns (all of them, if fewer exist).

    With fewer than ``WINDOW_MINUTES`` returns available — a short or
    heavily filtered series — the mean simply uses whatever is there,
    rather than failing or padding with invented values.
    """
    window = returns[-WINDOW_MINUTES:]
    return sum(window) / len(window)


def forecast_price(closes):
    """Forecast the price 240 minutes after the last close in ``closes``.

    With fewer than two usable closes there is no drift to measure, so
    the forecast is the last usable close (persistence); with none at
    all, the placeholder keeps the case valid. Otherwise the last hour's
    drift is extrapolated over the horizon at ``SHRINK_FACTOR`` strength.
    """
    if not closes:
        return FALLBACK_PRICE
    last_close = closes[-1]
    if len(closes) < 2:
        return last_close
    drift = recent_drift(log_returns(closes))
    extrapolated = drift * HORIZON_MINUTES * SHRINK_FACTOR
    return last_close * math.exp(extrapolated)


def clamp_to_grid(value):
    """Round a forecast to 5 decimals and clamp it into (0, 10,000,000).

    The clamp can only bind on an extreme extrapolated move; when it
    does, the case still gets a valid number instead of an invalid one.
    """
    bounded = min(MAX_PRICE, max(MIN_PRICE, value))
    scale = 10 ** PRICE_DECIMALS
    return round(bounded * scale) / scale


def write_forecast(output_dir, case_id, price):
    """Write one ``<case_id>.out`` file with exactly the required shape."""
    payload = {"forecasts": [{"case": case_id, "price": price}]}
    out_path = os.path.join(output_dir, case_id + ".out")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def process_case(input_dir, output_dir, filename):
    """Forecast one case file and write its output file."""
    case_id, raw_prices = load_case(os.path.join(input_dir, filename))
    price = clamp_to_grid(forecast_price(usable_closes(raw_prices)))
    write_forecast(output_dir, case_id, price)


def main():
    """Run every case in the input directory, in name order."""
    input_dir, output_dir = resolve_directories()
    os.makedirs(output_dir, exist_ok=True)
    for filename in list_case_files(input_dir):
        process_case(input_dir, output_dir, filename)


if __name__ == "__main__":
    main()
