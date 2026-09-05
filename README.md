# FiRecon — AI Finance Controller

FiRecon is an evidence-first payment reconciliation controller for a payment gateway. It reconciles payments against settlements, refunds, and bank credits, then explains the result in plain language for a finance operator.

It covers multiple scenarios such as exact matches, fee/tax deductions, full/partial refunds (with and without charges), partial settlements, batch settlements, missing/mismatched bank credits, duplicate payments, and settlement-integrity failures.

## Architecture
<img width="448" height="497" alt="firecon" src="https://github.com/user-attachments/assets/f6926b8a-2c3c-49db-8c92-4fa7c7c2d1ca" />

**Design Principle:** The financial decision is deterministic and evidence-based. AI is an analysis layer only, it explains the controller's result and does not decide whether a payment reconciles.


## How it works

FiRecon separates financial decisioning from AI analysis.

- **`core/evidence.py`** — builds the financial evidence for each payment.
- **`core/engine.py`** — deterministic reconciliation controller. It produces `MATCHED`, `EXPLAINED`, or `EXCEPTION` with a specific reason.
- **`core/analyst.py`** — uses Gemini to explain the controller's decision. Gemini never overrides the financial decision.
- **`finance_controller.py`** — runs the reconciliation flow.
- **`app/`** — Streamlit dashboard for processing and investigating payments.
- **`benchmark/`** — validation dataset and evaluation script.

## Run application

```bash
git clone https://github.com/me-hem/FiRecon     # Clone the repo
cd FiRecon                                      # Navigate to project root dir

pip install -r requirements.txt     # Install dependencies
python -m data.generate_data        # Generate synthetic data
streamlit run app/app.py            # Run FiRecon webapp

# Run Benchmark
python -m benchmark.evaluate
```

**Note: For AI explanations, configure the Gemini API key in .env file.**
```
LLM_API_KEY=YOUR-API-KEY
LLM_MODEL=gemini-3.6-flash
```

## Evaluation

FiRecon processes a batch of 56 synthetic payment records covering exact matches, fees and taxes, refunds, partial settlements, batch settlements, duplicate payments, missing bank credits, bank mismatches, and unexplained differences.

- **Match Rate:** 56 Payments processed, 10 Matched, 36 Explained and 46 Resolved without investigation (82.1%)
- **Measured Accuracy:** The deterministic reconciliation controller reproduced the expected decision in 56/56 cases (100%). This measures deterministic rule correctness on the synthetic benchmark, not production or AI-model accuracy.
- **Throughput:** 142.4 payments/sec, measured locally by processing the full batch through the controller (average over 5 iterations).
- **Exceptions:** Duplicate Payment, Bank Amount Mismatch, Missing Bank Credit, Unexplained Difference

## Future work

- The benchmark currently checks decision status only; checking the exact reason too would catch cases where the status is right for the wrong reason.

