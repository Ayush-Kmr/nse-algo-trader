"""Angel One SmartAPI adapter: deliberately NOT built yet.

Live orders through SmartAPI are algo orders under NSE's retail-algo rules. Before this exists:
- a static IP registered in the SmartAPI dashboard (GitHub Actions runners cannot provide one: use a VPS),
- algo order tagging, LIMIT / SL-L orders only (no MARKET, no IOC),
- broker-resident stop placed the moment an entry fills, plus a separate supervisor process,
- positive net out-of-sample expectancy from the backtester, and 30+ forward paper sessions.
See docs/UNATTENDED_DESIGN.md.
"""


class AngelOneBroker:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "LIVE trading is not built. It needs a static-IP VPS, algo tagging and a passed "
            "backtest gate first. See docs/UNATTENDED_DESIGN.md."
        )
