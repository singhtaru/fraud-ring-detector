"""USD per unit of each currency, as derived by fx_rates.py (median observed rate).

The same map was used to build FLOWS_TO.usd (graph_queries/4a1), so keeping
FLOWS_TO in sync after an API write must use these exact values.
"""
from typing import Literal

USD_PER_UNIT = {
    "Australian Dollar": 0.707814, "Bitcoin": 11874.4, "Brazil Real": 0.177101,
    "Canadian Dollar": 0.757978, "Euro": 1.17178, "Mexican Peso": 0.0472968,
    "Ruble": 0.0128528, "Rupee": 0.0136158, "Saudi Riyal": 0.266588,
    "Shekel": 0.296121, "Swiss Franc": 1.0929, "UK Pound": 1.29166,
    "US Dollar": 1, "Yen": 0.00948767, "Yuan": 0.149307,
}

Currency = Literal[
    "Australian Dollar", "Bitcoin", "Brazil Real", "Canadian Dollar", "Euro",
    "Mexican Peso", "Ruble", "Rupee", "Saudi Riyal", "Shekel", "Swiss Franc",
    "UK Pound", "US Dollar", "Yen", "Yuan",
]
