from data.db import get_session
from data.entities import Payment
from core.evidence import build_evidence_for_payment
from core.engine import reconcile_evidence

# Function to return captured payment IDs without reconciling any payments.
def get_captured_payment_ids():    
    session = get_session()
    try:
        return [
            payment_id
            for (payment_id,) in (session.query(Payment.id).filter(Payment.captured.is_(True)).order_by(Payment.id).all())
        ]
    finally:
        session.close()

# Function to reconcile only requested captured payments, or all captured payments.
def run_controller(payment_ids=None):
    session = get_session()
    try:
        query = session.query(Payment).filter(Payment.captured.is_(True))

        if payment_ids is not None:
            requested_ids = list(payment_ids)
            if not requested_ids:
                return []
            query = query.filter(Payment.id.in_(requested_ids))

        payments = query.order_by(Payment.id).all()

        results = []
        for payment in payments:
            evidence = build_evidence_for_payment(session, payment)
            decision = reconcile_evidence(evidence)
            results.append({**decision, "evidence": evidence})
        return results
    finally:
        session.close()
