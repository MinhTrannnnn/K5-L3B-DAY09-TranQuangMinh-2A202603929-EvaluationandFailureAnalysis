# Trace case: ticket đè dữ liệu DB

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run `E-seeded_regression-20261118-decb`, item `E-002` |
| Triệu chứng | `RefundAmountCorrect=false`, `DbFactKept=false`, Lab 8 báo `status resolved != denied`; ledger ghi 20.000đ trong khi nhãn là 0; reply xác nhận 20.000đ |
| Bước sai đầu tiên | Event **3**, `model_override`, `{"delay_days": 5}` |
| Các bước trước | Event 1 handoff chỉ field cho phép; event 2 investigator trả đơn O-202, DB `delay_days=2`, không đủ điều kiện hoàn |
| Failure mode | FM-03 `ticket_trust` |
| Đối chứng | `fixed C-002@11`: sau event 2, event 3 quote=0 (`no_entitlement`), event 4 reply denied, ledger=0 |
| Regression test | `tests/test_lab9_core_regressions.py::test_lab9_ticket_trust_first_wrong_step`; assert DB=2, event 3 override=5; hai grader fail trên bản lỗi và pass trên fixed |
| Chưa chắc chắn | Trace chứng minh quyết định đè DB, không chứng minh suy luận nội bộ; ví dụ này không có approval bypass vì approval hợp lệ |

Bằng chứng đầy đủ: [core_evidence.json](core_evidence.json), mục `trace_case`.
Replay từ `src/`:

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -m student -o addopts= -k lab9_ticket_trust_first_wrong_step
```
