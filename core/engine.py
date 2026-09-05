from data.db import get_session
from data.entities import Payment
from core.evidence import build_evidence_for_payment
from core.money import ZERO


def _result(payment_id, status, reason):
    return {"payment_id": payment_id, "status": status, "reason": reason}


def _first_settlement_failure(evidence):
    for settlement in evidence["settlement_evidence"]:
        if settlement["settlement_currency"] != evidence["payment_currency"]:
            return "CURRENCY_MISMATCH"
        if settlement["settlement_status"] != "processed":
            return "SETTLEMENT_NOT_PROCESSED"
        if not settlement["settlement_txn_settled"]:
            return "SETTLEMENT_TXN_NOT_SETTLED"
        if not settlement["settlement_integrity"]:
            return "UNEXPLAINED_DIFFERENCE"

    for settlement in evidence["settlement_evidence"]:
        if not settlement["bank_credit_present"]:
            return "MISSING_BANK_CREDIT"
        if not settlement["bank_integrity"]:
            invalid_types = any(
                txn["currency"] != settlement["settlement_currency"]
                or txn["transaction_type"] != "CREDIT"
                for txn in settlement["bank_transactions"]
            )
            return "BANK_TRANSACTION_INVALID" if invalid_types else "BANK_AMOUNT_MISMATCH"
    return None


def reconcile_evidence(evidence):
    payment_id = evidence["payment_id"]
    payment_amount = evidence["payment_amount"]

    if evidence["duplicate_detected"]:
        return _result(payment_id, "EXCEPTION", "DUPLICATE_PAYMENT")

    settlement_failure = _first_settlement_failure(evidence)
    if settlement_failure:
        return _result(payment_id, "EXCEPTION", settlement_failure)

    processed_refunds = evidence["processed_refunds"]
    if any(r["currency"] != evidence["payment_currency"] for r in processed_refunds):
        return _result(payment_id, "EXCEPTION", "CURRENCY_MISMATCH")

    total_refund = evidence["total_refund"]
    if total_refund > payment_amount:
        return _result(payment_id, "EXCEPTION", "REFUND_EXCEEDS_PAYMENT")
    if total_refund == payment_amount:
        return _result(payment_id, "EXPLAINED", "FULL_REFUND")
    if total_refund > ZERO:
        return _result(payment_id, "EXPLAINED", "PARTIAL_REFUND")

    payment_settlement_count = sum(
        any(txn["payment_id"] == payment_id for txn in settlement["settlement_transactions"])
        for settlement in evidence["settlement_evidence"]
    )
    if payment_settlement_count > 1:
        return _result(payment_id, "EXPLAINED", "PARTIAL_SETTLEMENT")

    has_batch_settlement = any(
        settlement["is_batch_settlement"]
        for settlement in evidence["settlement_evidence"]
    )
    if has_batch_settlement:
        return _result(payment_id, "EXPLAINED", "BATCH_SETTLEMENT")

    total_fee = evidence["total_fee"]
    total_tax = evidence["total_tax"]
    settled_amount = evidence["settled_amount"]
    expected_net = evidence["expected_net"]

    if (total_fee > ZERO or total_tax > ZERO) and settled_amount == expected_net:
        return _result(payment_id, "EXPLAINED", "FEE_TAX_EXPLAINED")

    if settled_amount == expected_net and total_fee == ZERO and total_tax == ZERO:
        return _result(payment_id, "MATCHED", "EXACT_MATCH")

    return _result(payment_id, "EXCEPTION", "UNEXPLAINED_DIFFERENCE")


def reconcile_payment(session, payment):
    return reconcile_evidence(build_evidence_for_payment(session, payment))


def reconcile_all():
    session = get_session()
    try:
        payments = (session.query(Payment).filter(Payment.captured.is_(True)).order_by(Payment.id).all())
        return [reconcile_payment(session, payment) for payment in payments]
    finally:
        session.close()


if __name__ == "__main__":
    results = reconcile_all()
    print(f"Reconciled {len(results)} captured payments.")
    for result in results:
        print(f"Payment {result['payment_id']}: {result['status']} / {result['reason']}")
