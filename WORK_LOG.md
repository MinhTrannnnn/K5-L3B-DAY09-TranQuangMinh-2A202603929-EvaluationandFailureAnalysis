# Nhật ký thực hiện Lab 9 Core

Ngày: 2026-11-18 (Asia/Ho_Chi_Minh). Người thực hiện: Trần Quang Minh.
Nhật ký ghi thay đổi, lệnh và kết quả; không phải bản ghi suy luận nội bộ.

## Chuẩn bị
- Tải repo gốc Day 8; chép 63 file từ `src/`, đối chiếu nội dung khớp bản gốc.
- Tạo `src/.venv` bằng Python 3.12, cài hai file requirements; smoke test: M0 PASS.
- Giữ nguyên `src/lab8/`, variant, trap và các test được cung cấp.

## Core đang thực hiện
- M1: mapping failure modes cho 14 item; nhãn tách riêng, provenance tới trace evidence.
- M2: confusion (FAIL là positive), precision/recall, Cohen κ, Rogan–Gladen.
- M3: grader approval, ledger amount; thêm `reply_amount_correct` đối chiếu reply với ledger.
- M4: paired percentile bootstrap bằng SciPy, 1.000 resample, RNG 2027, CI 95%.
- Metric spec v1.1: thêm metric FM-08 blocking; giữ nguyên ngưỡng có sẵn.

Kết quả kiểm tra và bằng chứng sẽ được bổ sung sau khi chạy.

## Kết quả hoàn tất Core local

- Chạy từ `src/`: `.venv/bin/python -m scripts.verify_core`.
- 16/16 bước đúng exit code mong đợi. Output đầy đủ: `logs/core_checks.log` (có thời gian theo Asia/Ho_Chi_Minh).
- Test học viên Core: 20 passed; bao gồm test mới về bước sai đầu tiên C-002, FM-08 ledger đúng/reply sai, định dạng tiền và approval không ghi tiền.
- Test host mặc định của repo gốc: đạt; số lượng và thời gian nằm trong log.
- Eval set v1: 14 item, SHA `decb82dc4db1`, check 0 problem; nhãn tách riêng.
- Judge tone đạt (κ 0.757, P 0.857, R 0.8); helpful không đạt (κ 0.375, R 0.3). Exit 1 của helpful là kết quả đúng mong đợi.
- Chạy 8 anchor lỗi bằng công tắc có sẵn của `make_shape`: bắt 8/8; đối chứng 14 fixed@11: 0 báo nhầm. Không suy rộng kết quả này sang dữ liệu chưa thấy.
- Baseline swarm pass_rate 0.9857; fixed 1.0, gate exit 0; seeded_regression 0.7143, gate exit 1 và có `pass_rate`.
- Paired Δ pass_rate regression −0.271; CI [−0.500, −0.057], khớp tham chiếu.
- Báo cáo chỉ sinh bằng `lab9.eval`: `src/reports/baseline_v1.json`, `eval_pr.json`, `eval_fixed.json`, `eval_seeded_regression.json`.
- Hoàn thiện 5 docs bắt buộc; bảng metric/CI được script lấy từ report. `src/harness_map.yaml` v1.2 có section eval.
- Bằng chứng trace/judge: `docs/core_evidence.json`, sinh bằng `python -m scripts.core_evidence`.
- Tài liệu có thể tái sinh: `python -m scripts.build_core_docs`. Nội dung PR có sẵn tại `docs/PR_CORE.md`.
- `git diff --check` sạch; 28 file `src/lab8/` khớp byte với repo gốc. Không sửa variant/trap/test có sẵn.

## Trạng thái sau Core (trước yêu cầu làm nâng cao)

Code và bằng chứng đã hoàn tất trên máy; chưa commit/push, mở PR hoặc merge, chưa có kết quả GitHub Actions.
`gh auth status` trong môi trường hiện tại báo token không hợp lệ, nên chưa xác nhận được truy cập GitHub đã đăng nhập.
Trước khi nộp, chủ bài cần rà soát tài liệu/audit do Codex hỗ trợ. Sau đó commit toàn bộ thay đổi (nhớ `git add -f src/reports/*.json`), đẩy nhánh `starter/d09`, mở PR trong fork về `main`, dùng `docs/PR_CORE.md` làm mô tả, đợi `eval-gate` xanh và merge trước hạn LMS.
Không có key anchor/hidden tests của giảng viên; chưa xác nhận điểm số cuối cùng. Advanced/Expert nằm ngoài phạm vi lần này.

## Advanced / Expert M5–M7 (yêu cầu tiếp theo của chủ bài)

- Tiếp tục hoàn toàn trên máy; giữ yêu cầu chưa push, không mở PR hoặc merge.
- M5: điền 8 mapping cơ chế → FM; sinh v2 gồm 28 item (14 public + 14 adversarial), SHA `38ce500198f1`; mọi FM bị tấn công có ≥3 item. Thêm slices money_movement/adversarial cùng denial, tất cả blocking.
- M6: cài pass@k/pass^k với kiểm tra input; đối chiếu bằng liệt kê tổ hợp độc lập. A/A hai bộ seed cho mọi Δ=0; pass_hat_5=0.8929, sàn 0.85 (≥0.8). Tài liệu phân biệt mức tuyệt đối và nhiễu Δ, nêu giới hạn LLM thật và 5 seed.
- M7: kiểm PR và baseline về NaN/inf/None, grader crash, số dòng, cặp trùng, đủ ma trận item×seed, tập cặp, slice tag và summary so với rows. Ratchet cần `--base-spec` tin cậy; không cho bỏ/nới metric, slice, blocking hoặc no_significant_drop trên cùng eval-set version.

### Sửa thiếu sót phát hiện khi kiểm rộng hơn

Kiểm 8 anchor lỗi đã chọn trước đó đạt 8/8 nhưng không thay thế kiểm toàn bộ trial lỗi. Lệnh chính thức `lab9.mutation --detect` ban đầu chỉ đạt 75%, do C-013 có proposal sai dù ledger vẫn 0.
Đã thêm `ProposalAmountCorrect`, test hồi quy cho C-013 và metric `proposal_amount_correct`. Kết quả kiểm lại: detection 100%, false alarms 0%.
Metric spec v1 tăng 1.1 → 1.2; v2 là 2.1. Không nới các ngưỡng v1 đã có. Log lần chạy phát hiện lỗi được giữ ở `logs/advanced_checks_initial.log`; kết quả cuối ở `logs/advanced_checks.log`.

### Bằng chứng và kiểm tra

- `python -m scripts.verify_advanced` chạy lại Core, test Advanced, detection, eval v2, A/A, baseline tự so sánh, 5 variant và 4 trap với exit code cụ thể.
- Mutation score: 3/3 regression bị chặn; 0 báo nhầm (`fixed`, `honest_refactor` đều merge).
- `slice_regression` chỉ bị chặn ở `slice:money_movement/pass_rate`; `flaky_regression` bị chặn qua pass_hat_5 cùng các kiểm tra liên quan.
- Bốn trap công khai đều exit 1 với INTEGRITY/ratchet; trap builder tổng hợp exit 0 nghĩa là bắt đủ.
- Test bổ sung: dòng trùng giữ nguyên số dòng, lỗi evaluator trên report xanh, giả summary, đổi slice, sửa manifest seed, ratchet metric/slice, quiet_override không event, và baseline một item so với chính nó.
- Các report mới đều sinh qua `lab9.eval`; các trap sinh qua `lab9.traps`, không sửa tay.
- Eval card và PRD có phần Advanced/Expert; taxonomy bổ sung trace kiểm cross-principal v2. `docs/PR_LAB09.md` chứa nội dung PR đầy đủ, output mutation/A/A và bốn trap.
- `docs/advanced_checks.json`: lệnh/output/exit; `docs/advanced_evidence.json`: số liệu và trace v2. Tài liệu có script tái sinh; kết quả GitHub và hidden tests chưa được xác nhận.
- Đã đối chiếu 28 file gốc `src/lab8/` không đổi; không sửa variant, trap hoặc test được cung cấp.

### Kết quả xác nhận cuối cùng

- Chạy lại `python -m scripts.verify_advanced` sau các sửa đổi: **24/24 checks passed** (bao gồm runner Core **16/16**).
- Test Core: **21 passed**; test Advanced/Expert: **38 passed**; bộ test host mặc định: **57 passed**.
- Detection trên toàn bộ seeded_regression lỗi: **100%**; false alarms fixed: **0%**. Mutation **3/3**, false alarms **0**; bốn trap đều bị chặn.
- Bản hiện tại đã hoàn thành M0–M7 và tài liệu/bằng chứng local. Chưa commit/push/PR/merge; chưa chạy CI GitHub hoặc bộ chấm ẩn. Không cam kết điểm 100 từ kết quả công khai.

## Chuẩn bị push theo yêu cầu chủ bài

- Chủ bài đã yêu cầu push; tạo nhánh `starter/d09`, commit toàn bộ code/tài liệu/log và force-add report v1/v2 cùng trap được script sinh.
- Xác nhận GitHub CLI đăng nhập được tài khoản `MinhTrannnnn` khi chạy ngoài sandbox. Thông báo token không hợp lệ trước đó chỉ xuất hiện trong môi trường sandbox, không phản ánh phiên đăng nhập kiểm tra lần này.
- Nhánh remote `main` đang ở commit gốc `9e1549a`; chưa có remote `starter/d09` khi kiểm tra.
- Không merge vào `main`; GitHub Actions chỉ được xác nhận khi có lần chạy thực tế trên GitHub.
