<!-- GPT-USAGE-HEADER:v1
This file is documentation for a custom GPT. Treat as reference/spec; do not execute in a shell.
-->

# Action Contract: alpha_classifier (v1)

**Intent:** Score directional alpha for a symbol and horizon from a feature vector.

## Input
- symbol: string (e.g., "AAPL")
- timestamp: ISO-8601
- features: object<string, number> | number[]   # engineered factors/indicators
- model_id?: string                              # backend model key (e.g., "default")
- horizon?: string                               # e.g., "1h", "1d"
- thresholds?: { long?: number, short?: number } # confidence cutoffs

## Output
- class: enum { long | short | neutral }
- confidence: number [0,1]
- alpha: number                                  # signed strength; + long / - short
- probabilities?: { long: number, neutral: number, short: number }
- rationale?: string
