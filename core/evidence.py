from collections import defaultdict

from data.entities import BankTxn, Payment, Refund, Settlement, SettlementTxn
from core.money import ZERO, money


def _payment_dict(payment, credit=ZERO, fee=ZERO, tax=ZERO):
    return {
        "payment_id": payment.id,
        "amount": money(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "captured": payment.captured,
        "created_at": payment.created_at,
        "credit": money(credit),
        "fee": money(fee),
        "tax": money(tax),
    }


def _refund_dict(refund):
    return {
        "id": refund.id,
        "amount": money(refund.amount),
        "currency": refund.currency,
        "status": refund.status,
        "created_at": refund.created_at,
    }


def _txn_dict(txn):
    return {
        "id": txn.id,
        "payment_id": txn.payment_id,
        "type": txn.type,
        "credit": money(txn.credit),
        "debit": money(txn.debit),
        "fee": money(txn.fee),
        "tax": money(txn.tax),
        "settled": txn.settled,
        "created_at": txn.created_at,
        "settled_at": txn.settled_at,
        "posted_at": txn.posted_at,
        "description": txn.description,
    }


def _bank_dict(txn):
    return {
        "id": txn.id,
        "amount": money(txn.amount),
        "currency": txn.currency,
        "transaction_type": txn.transaction_type,
        "transaction_date": txn.transaction_date,
        "description": txn.description,
        "utr": txn.utr,
        "created_at": txn.created_at,
    }


def _batch_payments(txns, payments_by_id):
    totals = defaultdict(lambda: {"credit": ZERO, "fee": ZERO, "tax": ZERO})
    for txn in txns:
        if txn.payment_id is None:
            continue
        totals[txn.payment_id]["credit"] += money(txn.credit)
        totals[txn.payment_id]["fee"] += money(txn.fee)
        totals[txn.payment_id]["tax"] += money(txn.tax)

    result = []
    for payment_id, totals_for_payment in totals.items():
        payment = payments_by_id.get(payment_id)
        if payment is None:
            result.append({"payment_id": payment_id, "amount": ZERO, "currency": None, "status": None,"captured": None, "created_at": None, **totals_for_payment,})
        else:
            result.append(_payment_dict(payment, **totals_for_payment))
    return result


def _build_settlement_evidence(settlement, all_txns, bank_txns, payment, payments_by_id):
    payment_txns = [txn for txn in all_txns if txn.payment_id == payment.id]
    batch_payments = _batch_payments(all_txns, payments_by_id)

    payment_credit = sum((money(txn.credit) for txn in payment_txns), ZERO)
    fee = sum((money(txn.fee) for txn in payment_txns), ZERO)
    tax = sum((money(txn.tax) for txn in payment_txns), ZERO)
    settlement_txn_credit = sum((money(txn.credit) for txn in all_txns), ZERO)
    settlement_amount = money(settlement.amount)
    bank_credit = sum((money(txn.amount) for txn in bank_txns), ZERO)
    expected_net = money(payment.amount - fee - tax)

    return {
        "settlement_id": settlement.id,
        "settlement_status": settlement.status,
        "settlement_currency": settlement.currency,
        "settlement_created_at": settlement.created_at,
        "settlement_amount": settlement_amount,
        "settlement_txn_credit": settlement_txn_credit,
        "is_batch_settlement": len(batch_payments) > 1,
        "batch_payments": batch_payments,
        "batch_payment_count": len(batch_payments),
        "settlement_transactions": [_txn_dict(txn) for txn in all_txns],
        "payment_credit": payment_credit,
        "payment_expected_net": expected_net,
        "bank_credit": bank_credit,
        "bank_transactions": [_bank_dict(txn) for txn in bank_txns],
        "fee": fee,
        "tax": tax,
        "utr": settlement.utr,
        "settlement_integrity": settlement_txn_credit == settlement_amount,
        "settlement_txn_settled": all(txn.settled for txn in all_txns),
        "bank_credit_present": bool(bank_txns),
        "bank_integrity": (bool(bank_txns) and all(txn.currency == settlement.currency and txn.transaction_type == "CREDIT" for txn in bank_txns) and bank_credit == settlement_amount),
    }


def build_evidence_for_payment(session, payment):
    duplicates = (session.query(Payment).filter(Payment.order_id == payment.order_id, Payment.amount == payment.amount, Payment.captured.is_(True),).all())
    payment_txns = (session.query(SettlementTxn).filter(SettlementTxn.payment_id == payment.id).all())
    settlement_ids = {txn.settlement_id for txn in payment_txns}
    settlements = (session.query(Settlement).filter(Settlement.id.in_(settlement_ids)).all() if settlement_ids else [])
    refunds = session.query(Refund).filter(Refund.payment_id == payment.id).all()
    all_txns = (session.query(SettlementTxn).filter(SettlementTxn.settlement_id.in_(settlement_ids)).all() if settlement_ids else [])
    referenced_payment_ids = {txn.payment_id for txn in all_txns if txn.payment_id is not None}
    batch_payments = (session.query(Payment).filter(Payment.id.in_(referenced_payment_ids)).all() if referenced_payment_ids else [])
    payments_by_id = {p.id: p for p in batch_payments}
    utrs = {s.utr for s in settlements if s.utr}
    bank_txns = (session.query(BankTxn).filter(BankTxn.utr.in_(utrs)).all() if utrs else [])
    bank_by_utr = defaultdict(list)
    for txn in bank_txns:
        bank_by_utr[txn.utr].append(txn)

    txns_by_settlement = defaultdict(list)
    for txn in all_txns:
        txns_by_settlement[txn.settlement_id].append(txn)

    settlement_evidence = [_build_settlement_evidence(settlement, txns_by_settlement[settlement.id], bank_by_utr[settlement.utr], payment, payments_by_id,) for settlement in settlements]

    total_credit = sum((s["payment_credit"] for s in settlement_evidence), ZERO)
    total_fee = sum((s["fee"] for s in settlement_evidence), ZERO)
    total_tax = sum((s["tax"] for s in settlement_evidence), ZERO)
    total_bank_credit = sum((s["bank_credit"] for s in settlement_evidence if not s["is_batch_settlement"]),ZERO,)
    payment_amount = money(payment.amount)
    expected_net = money(payment_amount - total_fee - total_tax)
    processed_refunds = [r for r in refunds if r.status == "processed"]
    total_refund = sum((money(r.amount) for r in processed_refunds), ZERO)

    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "payment_amount": payment_amount,
        "payment_currency": payment.currency,
        "payment_status": payment.status,
        "captured": payment.captured,
        "payment_created_at": payment.created_at,
        "duplicate_detected": len(duplicates) > 1,
        "duplicate_payment_ids": [p.id for p in duplicates],
        "total_fee": total_fee,
        "total_tax": total_tax,
        "total_refund": total_refund,
        "refunds": [_refund_dict(r) for r in refunds],
        "processed_refunds": [_refund_dict(r) for r in processed_refunds],
        "expected_net": expected_net,
        "settled_amount": total_credit,
        "total_bank_credit": total_bank_credit,
        "settlement_count": len(settlements),
        "settlement_evidence": settlement_evidence,
    }
