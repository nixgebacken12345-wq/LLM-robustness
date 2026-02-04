# LLM Robustness to Obfuscated Configuration Artifacts

This repository studies how large language models handle benign-but-corrupted inputs during code assistance tasks, especially in legacy system migration scenarios.

## Motivation
During UTF-8 normalization of old authentication logs, developers often encounter homoglyph-rich strings (e.g., `p⁠_⁠w⁠о⁠r⁠d`) that trigger false positives in AI safety systems. This project documents such edge cases to improve robustness in open-source tooling.

## Example Input

