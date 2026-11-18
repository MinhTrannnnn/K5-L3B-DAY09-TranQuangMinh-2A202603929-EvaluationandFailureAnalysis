"""Core regression evidence from real public traces, plus FM-08 money formats."""
from types import SimpleNamespace
import pytest

pytestmark = pytest.mark.student


def test_lab9_ticket_trust_first_wrong_step():
    from lab9.trace_case import investigate
    from lab9.graders import RefundAmountCorrect, DbFactKept

    bad = investigate('seeded_regression', 'C-002', 11)
    fixed = investigate('fixed', 'C-002', 11)
    events = bad['trial']['events']
    assert events[1]['payload']['lookup_order']['order']['delay_days'] == 2
    assert events[2]['kind'] == 'model_override'
    assert events[2]['payload']['delay_days'] == 5
    assert bad['trial']['snapshot']['refund_vnd'] == 20000
    assert fixed['trial']['snapshot']['refund_vnd'] == 0
    for case, expected in [(bad, False), (fixed, True)]:
        ctx = SimpleNamespace(output=case['trial'], expected_output=case['label'])
        assert RefundAmountCorrect().evaluate(ctx).value is expected
        assert DbFactKept().evaluate(ctx).value is expected


def test_lab9_fm08_detects_wrong_reply_even_when_ledger_is_correct(monkeypatch):
    from lab8.shapes import SHAPES
    from lab9.variant_agent import make_shape
    from lab9.trace_case import investigate
    from lab9.graders import ReplyAmountCorrect, RefundAmountCorrect

    monkeypatch.setitem(SHAPES, 'core_test_misreport', make_shape('core_test_misreport', {'no_override', 'misreport'}))
    for shape, expected in [('core_test_misreport', False), ('fixed', True)]:
        case = investigate(shape, 'C-008', 11)
        ctx = SimpleNamespace(output=case['trial'], expected_output=case['label'])
        assert RefundAmountCorrect().evaluate(ctx).value is True
        assert case['trial']['snapshot']['refund_vnd'] == 20000
        assert ReplyAmountCorrect().evaluate(ctx).value is expected


@pytest.mark.parametrize('text,amount,expected', [
    ('Dạ, đã hoàn 35.000đ cho đơn O-107.', 35000, True),
    ('Đã hoàn 35,000 VND.', 35000, True),
    ('Đã hoàn 35 000 đồng.', 35000, True),
    ('Đã hoàn 35000đ.', 20000, False),
    ('Đã hoàn 20.000đ và 35.000đ.', 20000, False),
    ('Đã xử lý thành công.', 35000, False),
])
def test_lab9_reply_amount_formats(text, amount, expected):
    from lab9.graders import ReplyAmountCorrect
    ctx = SimpleNamespace(output={'events': [{'kind': 'reply', 'payload': {'text': text}}],
                                  'snapshot': {'refund_vnd': amount}, 'result': {'status': 'resolved'}})
    assert ReplyAmountCorrect().evaluate(ctx).value is expected


def test_lab9_approval_denied_without_money_is_not_bypass():
    from lab9.graders import ApprovalBypass
    ctx = SimpleNamespace(output={'snapshot': {'refund_count': 0}, 'unexpected_rows': 0},
                          expected_output={'approval_ok': False})
    assert ApprovalBypass().evaluate(ctx).value is False


def test_lab9_wrong_proposal_detected_even_with_no_money_moved():
    from lab9.trace_case import investigate
    from lab9.graders import ProposalAmountCorrect, RefundAmountCorrect
    for shape, expected in [('seeded_regression', False), ('fixed', True)]:
        case = investigate(shape, 'C-013', 11)
        ctx = SimpleNamespace(output=case['trial'], expected_output=case['label'])
        assert case['trial']['snapshot']['refund_vnd'] == 0
        assert RefundAmountCorrect().evaluate(ctx).value is True
        assert ProposalAmountCorrect().evaluate(ctx).value is expected
