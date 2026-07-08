# Evaluation Harness

The vindex evaluation harness provides quantitative correctness checks of compiled outputs against curated, ground-truth expected stubs (golden fixtures).

## CLI Command

To run evaluation on compiled outputs:

```bash
vindex eval path/to/fixture_001 path/to/compiled_output/
```

### Metrics Computed

1. **ASR Jaccard Accuracy:** Word-level Jaccard similarity between transcribed speech.
2. **OCR Jaccard Accuracy:** Set Jaccard word similarity between text detected on sampled keyframes.
3. **Scene Boundaries F1-Score:** Measures boundary precision and recall (using a default 500ms match tolerance window).

## Exit Codes and CI Integration

The `vindex eval` command exits with:
- `0` if the overall score is `>= 85.0%` (Pass).
- `1` if the overall score is `< 85.0%` (Fail).

This enables gating PRs and builds in automated workflows to prevent regression.
