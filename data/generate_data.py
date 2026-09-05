from datetime import UTC, datetime, timedelta
from decimal import Decimal
import random
import csv

from data.db import create_tables, get_session
from core.money import money
from data.entities import (
    Customer,
    Order,
    Payment,
    Refund,
    Settlement,
    SettlementTxn,
    BankTxn,
)


random.seed(1351)

EXPECTED_SCENARIOS = {
    "normal": ("MATCHED", "EXACT_MATCH"),
    "fee_tax": ("EXPLAINED", "FEE_TAX_EXPLAINED"),
    "full_refund": ("EXPLAINED", "FULL_REFUND"),
    "partial_refund": ("EXPLAINED", "PARTIAL_REFUND"),
    "full_refund_charges": ("EXPLAINED", "FULL_REFUND"),
    "partial_refund_charges": ("EXPLAINED", "PARTIAL_REFUND"),
    "partial_settlement": ("EXPLAINED", "PARTIAL_SETTLEMENT"),
    "missing_bank": ("EXCEPTION", "MISSING_BANK_CREDIT"),
    "bank_mismatch": ("EXCEPTION", "BANK_AMOUNT_MISMATCH"),
    "duplicate_payment": ("EXCEPTION", "DUPLICATE_PAYMENT"),
    "settlement_integrity": ("EXCEPTION", "UNEXPLAINED_DIFFERENCE"),
    "batch": ("MATCHED", "EXACT_MATCH"),
}


def record_ground_truth(session, ground_truth, known_payment_ids, scenario):
    payments = session.query(Payment).order_by(Payment.id).all()
    new_payments = [
        payment
        for payment in payments
        if payment.id not in known_payment_ids
    ]

    expected_status, expected_reason = EXPECTED_SCENARIOS[scenario]

    for payment in new_payments:
        ground_truth.append({
            "payment_id": payment.id,
            "scenario": scenario,
            "expected_status": expected_status,
            "expected_reason": expected_reason,
        })
        known_payment_ids.add(payment.id)


def write_ground_truth(ground_truth):
    path = "benchmark/ground_truth.csv"

    ground_truth = sorted(ground_truth, key=lambda row: row["payment_id"],)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "payment_id",
                "scenario",
                "expected_status",
                "expected_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(ground_truth)

    print(f"Ground truth: {path} ({len(ground_truth)} records)")


def calculate_fee_tax(amount):
    fee = money(amount * Decimal("0.03"))
    tax = money(fee * Decimal("0.18"))
    return fee, tax


# Basic record helpers

def add_customer(session, idx):
    customer = Customer(name=f"Customer {idx}", email=f"customer{idx}@mail.com",)
    session.add(customer)
    session.flush()
    return customer


def add_order(session, customer, amount, idx):
    order = Order(customer_id=customer.id, amount=money(amount), currency="INR", status="paid",)
    session.add(order)
    session.flush()
    return order


def add_payment(session, order, amount):
    payment = Payment(order_id=order.id, amount=money(amount), currency="INR", status="captured", captured=True, fee=Decimal("0.00"), tax=Decimal("0.00"),)
    session.add(payment)
    session.flush()
    return payment


def add_settlement(session, amount, settlement_idx, fee=Decimal("0.00"), tax=Decimal("0.00"),):
    settlement = Settlement(amount=money(amount), currency="INR", status="processed", fee=money(fee), tax=money(tax), utr=f"UTR{settlement_idx:06d}",)
    session.add(settlement)
    session.flush()
    return settlement


def add_settlement_txn(session, settlement, payment, order, amount, txn_type="payment",fee=Decimal("0.00"), tax=Decimal("0.00"), settled=True, settled_at=None, description=None,):
    txn = SettlementTxn(settlement_id=settlement.id, type=txn_type, amount=money(amount),debit=Decimal("0.00"), credit=money(amount), fee=money(fee), tax=money(tax),payment_id=payment.id if payment else None,order_id=order.id if order else None,settled=settled, settled_at=settled_at, posted_at=settled_at, description=description,)
    session.add(txn)
    session.flush()
    return txn


def add_bank_txn(session, settlement, amount, transaction_date,):
    bank_txn = BankTxn(utr=settlement.utr, amount=money(amount), currency="INR",transaction_type="CREDIT", transaction_date=transaction_date, description=f"Settlement credit for {settlement.utr}",)
    session.add(bank_txn)
    session.flush()
    return bank_txn


def add_refund(session, payment, amount):
    refund = Refund(payment_id=payment.id, amount=money(amount), currency="INR",status="processed",)
    session.add(refund)
    session.flush()
    return refund


# Scenario helpers

def scenario_normal(session, idx, settlement_idx):
    amount = money(random.randint(1000, 10000))
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    settlement = add_settlement(session, amount, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    add_settlement_txn(session, settlement, payment, order, amount, settled_at=settled_at,)
    add_bank_txn(session,settlement, amount, settled_at,)


def scenario_fee_tax(session, idx, settlement_idx):
    amount = money(random.randint(3000, 12000))
    fee, tax = calculate_fee_tax(amount)
    net_amount = money(amount - fee - tax)
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    payment.fee = fee
    payment.tax = tax
    settlement = add_settlement(session, net_amount, settlement_idx, fee=fee, tax=tax,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    add_settlement_txn(session, settlement, payment, order, net_amount, fee=fee, tax=tax,settled_at=settled_at, description="Processing fee and tax deducted from settlement",)
    add_bank_txn(session, settlement, net_amount, settled_at,)


def scenario_full_refund(session, idx, settlement_idx, with_charges=False):
    amount = money(random.randint(3000, 10000))
    fee = Decimal("0.00")
    tax = Decimal("0.00")
    settlement_amount = amount

    if with_charges:
        fee, tax = calculate_fee_tax(amount)
        settlement_amount = money(amount - fee - tax)

    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    payment.fee = fee
    payment.tax = tax
    settlement = add_settlement(session, settlement_amount, settlement_idx, fee=fee, tax=tax,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    
    add_settlement_txn(session, settlement, payment, order, settlement_amount, fee=fee, tax=tax,settled_at=settled_at, description=("Payment settled after processing charges" if with_charges else "Payment fully settled"),)
    add_bank_txn(session, settlement, settlement_amount, settled_at,)

    # Refund occurs after settlement.
    add_refund(session, payment, amount,)


def scenario_partial_refund(session, idx, settlement_idx, with_charges=False):
    amount = money(random.randint(5000, 12000))
    fee = Decimal("0.00")
    tax = Decimal("0.00")
    settlement_amount = amount

    if with_charges:
        fee, tax = calculate_fee_tax(amount)
        settlement_amount = money(amount - fee - tax)

    refund_amount = money(amount * Decimal("0.30"))
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    payment.fee = fee
    payment.tax = tax
    settlement = add_settlement(session, settlement_amount, settlement_idx, fee=fee, tax=tax,)
    settled_at = datetime.now(UTC) + timedelta(days=1)

    add_settlement_txn(session, settlement, payment, order, settlement_amount, fee=fee, tax=tax, settled_at=settled_at, description=("Payment settled after processing charges"if with_charges else "Payment fully settled"),)
    add_bank_txn(session, settlement, settlement_amount, settled_at,)
    add_refund(session, payment, refund_amount,)


def scenario_partial_settlement(session, idx, settlement_idx):
    amount = money(random.randint(6000, 14000))
    fee, tax = calculate_fee_tax(amount)
    net_amount = money(amount - fee - tax)
    first_amount = money(net_amount * Decimal("0.60"))
    second_amount = money(net_amount - first_amount)
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    payment.fee = fee
    payment.tax = tax
    first_settlement = add_settlement(session, first_amount, settlement_idx, fee=fee, tax=tax,)
    second_settlement = add_settlement(session, second_amount, settlement_idx + 1000,)
    first_date = datetime.now(UTC) + timedelta(days=1)
    second_date = first_date + timedelta(days=2)

    add_settlement_txn(session, first_settlement, payment, order, first_amount, fee=fee, tax=tax, settled_at=first_date, description="First partial settlement",)
    add_settlement_txn(session, second_settlement, payment, order, second_amount,settled_at=second_date, description="Remaining partial settlement",)
    
    add_bank_txn(session, first_settlement, first_amount, first_date,)
    add_bank_txn(session, second_settlement, second_amount, second_date,)


def scenario_missing_bank(session, idx, settlement_idx):
    amount = money(random.randint(3000, 10000))
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    settlement = add_settlement(session, amount, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    add_settlement_txn(session, settlement, payment, order, amount, settled_at=settled_at,)


def scenario_bank_mismatch(session, idx, settlement_idx):
    amount = money(random.randint(5000, 12000))
    bank_amount = money(amount - Decimal("1000.00"))
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    settlement = add_settlement(session, amount, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    add_settlement_txn(session, settlement, payment, order, amount, settled_at=settled_at,)
    add_bank_txn(session, settlement, bank_amount, settled_at,)


def scenario_duplicate_payment(session, idx, settlement_idx):
    amount = money(random.randint(3000, 10000))
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    primary_payment = add_payment(session, order, amount,)
    settlement = add_settlement(session, amount, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)
    add_settlement_txn(session, settlement, primary_payment, order, amount, settled_at=settled_at,)
    add_bank_txn(session, settlement, amount, settled_at,)

    # Second captured payment for the same order and amount.
    add_payment(session, order, amount,)

def scenario_settlement_integrity(session, idx, settlement_idx):
    amount = money(random.randint(5000, 12000))
    difference = Decimal("500.00")
    customer = add_customer(session, idx)
    order = add_order(session, customer, amount, idx)
    payment = add_payment(session, order, amount)
    settlement = add_settlement(session, amount - difference, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)

    add_settlement_txn(session, settlement, payment, order, amount, settled_at=settled_at, description="Settlement ledger contains unexplained difference",)
    add_bank_txn(session, settlement, amount - difference, settled_at,)

def scenario_batch_settlement(session, start_idx, settlement_idx, payment_count=5,):
    amounts = [money(random.randint(1000, 8000)) for _ in range(payment_count)]
    settlement_total = sum(amounts, Decimal("0.00"),)
    settlement = add_settlement(session, settlement_total, settlement_idx,)
    settled_at = datetime.now(UTC) + timedelta(days=1)

    for offset, amount in enumerate(amounts):
        idx = start_idx + offset
        customer = add_customer(session, idx,)
        order = add_order(session, customer, amount, idx,)
        payment = add_payment(session, order, amount,)
        add_settlement_txn(session, settlement, payment, order, amount, settled_at=settled_at, description="Payment included in settlement batch",)

    # One bank credit represents the entire settlement batch.
    add_bank_txn(session, settlement, settlement_total, settled_at,)


def generate():
    create_tables()

    session = get_session()

    try:
        # Start completely clean.
        session.query(BankTxn).delete()
        session.query(SettlementTxn).delete()
        session.query(Refund).delete()
        session.query(Settlement).delete()
        session.query(Payment).delete()
        session.query(Order).delete()
        session.query(Customer).delete()

        settlement_idx = 1
        case_idx = 1
        ground_truth = []
        known_payment_ids = set()

        # 10 payments with normal exact matches
        for _ in range(10):
            scenario_normal(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "normal")
            case_idx += 1
            settlement_idx += 1

        # 6 payments with fee + tax deductions
        for _ in range(6):
            scenario_fee_tax(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "fee_tax")
            case_idx += 1
            settlement_idx += 1

        # 3 payments with full refunds
        for _ in range(3):
            scenario_full_refund(session, case_idx, settlement_idx, with_charges=False,)
            record_ground_truth(session, ground_truth, known_payment_ids, "full_refund")
            case_idx += 1
            settlement_idx += 1

        # 3 payments with partial refunds
        for _ in range(3):
            scenario_partial_refund(session, case_idx, settlement_idx, with_charges=False,)
            record_ground_truth(session, ground_truth, known_payment_ids, "partial_refund")
            case_idx += 1
            settlement_idx += 1

        # 3 payments with full refunds + deductions
        for _ in range(3):
            scenario_full_refund(session, case_idx, settlement_idx, with_charges=True,)
            record_ground_truth(session, ground_truth, known_payment_ids, "full_refund_charges")
            case_idx += 1
            settlement_idx += 1

        # 3 payments with partial refunds + deductions
        for _ in range(3):
            scenario_partial_refund(session, case_idx, settlement_idx, with_charges=True,)
            record_ground_truth(session, ground_truth, known_payment_ids, "partial_refund_charges")
            case_idx += 1
            settlement_idx += 1

        # 3 payments with partial settlements (Each payment has two settlements.)
        for _ in range(3):
            scenario_partial_settlement(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "partial_settlement")
            case_idx += 1
            settlement_idx += 2

        # 2 payments with missing bank credits
        for _ in range(2):
            scenario_missing_bank(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "missing_bank")
            case_idx += 1
            settlement_idx += 1

        # 2 payments with bank amount mismatches
        for _ in range(2):
            scenario_bank_mismatch(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "bank_mismatch")
            case_idx += 1
            settlement_idx += 1

        # 2 duplicate-payment scenarios (Each has TWO payment records.)
        for _ in range(2):
            scenario_duplicate_payment(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "duplicate_payment")
            case_idx += 2
            settlement_idx += 1

        # 2 payments with unexplained differences
        for _ in range(2):
            scenario_settlement_integrity(session, case_idx, settlement_idx,)
            record_ground_truth(session, ground_truth, known_payment_ids, "settlement_integrity")
            case_idx += 1
            settlement_idx += 1

        # 15 batch payments (total 3 batches, each with 5 payments.)
        for _ in range(3):
            scenario_batch_settlement(session, case_idx, settlement_idx, payment_count=5,)
            record_ground_truth(session, ground_truth, known_payment_ids, "batch")
            case_idx += 5
            settlement_idx += 1

        session.commit()

        if len(ground_truth) != session.query(Payment).count():
            raise RuntimeError(
                "Ground-truth record count does not match payment count: "
                f"{len(ground_truth)} != {session.query(Payment).count()}"
            )

        write_ground_truth(ground_truth)

        payment_count = session.query(Payment).count()
        settlement_count = session.query(Settlement).count()
        bank_count = session.query(BankTxn).count()

        print("FiRecon synthetic data generated.")
        print(f"Payment records: {payment_count}")
        print(f"Settlements: {settlement_count}")
        print(f"Bank transactions: {bank_count}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    generate()