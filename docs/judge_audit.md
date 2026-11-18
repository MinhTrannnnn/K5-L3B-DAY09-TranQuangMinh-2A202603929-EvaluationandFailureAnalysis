# Judge audit

Dữ liệu replay công khai, mỗi tiêu chí 100 dòng. FAIL là positive; floors: κ≥0.6, P≥0.8, R≥0.7.
Số liệu sinh từ `lab9.judge.calibrate`, lưu tại `core_evidence.json`.

| Tiêu chí | n | κ | Precision | Recall | Quyết định |
|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.8 | Có — dùng cho tone |
| helpful | 100 | 0.375 | 1.0 | 0.3 | Không — loại khỏi gate |

- tone: TP=24, FP=4, FN=6, TN=66; observed FAIL=0.28, Rogan–Gladen=0.3.
- helpful: TP=9, FP=0, FN=21, TN=70; observed FAIL=0.09, Rogan–Gladen=0.3.

## Audit nội dung các bất đồng

Đánh giá dưới đây do Codex hỗ trợ đối chiếu câu trả lời, ghi chú CSV và rubric; sinh viên cần đọc và chịu trách nhiệm trước khi nộp.
Nhãn human trong bảng là nhãn được cung cấp, không phải nhãn người mới do lần làm bài này tạo ra.

| Case | Reply | Judge | Human | Kết luận audit | Hành động sửa rubric |
|---|---|---|---|---|---|
| H-008 | Em đã hoàn tiền cho anh rồi nha, anh check giúp em. | PASS | FAIL | Đồng ý nhãn human theo rubric: xưng 'em' + 'nha', quá suồng sã với khách; judge coi là thân thiện | Rubric tone: quy định xưng hô trang trọng; cho phép từ refund và câu ngắn nếu vẫn lịch sự. |
| H-017 | Dạ, bạn ơi LogiX đã hoàn 25.000đ cho đơn O-606 rồi nha. | PASS | FAIL | Đồng ý nhãn human theo rubric: xưng 'bạn' với khách lớn tuổi; judge coi là thân thiện | Rubric tone: quy định xưng hô trang trọng; cho phép từ refund và câu ngắn nếu vẫn lịch sự. |
| H-029 | Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm. | PASS | FAIL | Đồng ý nhãn human theo rubric: giọng ra lệnh ('không cần nhắn thêm'); judge chỉ thấy 'Dạ, vui lòng' | Rubric tone: quy định xưng hô trang trọng; cho phép từ refund và câu ngắn nếu vẫn lịch sự. |
| H-042 | Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ. | FAIL | PASS | Đồng ý nhãn human theo rubric: ngắn nhưng đủ ý; judge phạt vì 'thiếu xin lỗi' | Rubric tone: quy định xưng hô trang trọng; cho phép từ refund và câu ngắn nếu vẫn lịch sự. |
| H-051 | Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ. | FAIL | PASS | Đồng ý nhãn human theo rubric: dùng từ 'refund' — CS LogiX cho phép; judge phạt vì tiếng Anh | Rubric tone: quy định xưng hô trang trọng; cho phép từ refund và câu ngắn nếu vẫn lịch sự. |
| HL-015 | Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ. | PASS | FAIL | Đồng ý nhãn human theo rubric: ledger ghi 40.000đ | Rubric helpful: bắt buộc đúng số tiền/trạng thái, trả lời trực tiếp hoặc hỏi đúng thông tin thiếu; lời xin lỗi không đủ. |
| HL-016 | Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. LogiX đã hoàn 55.000đ cho đơn O-404. Một lần nữa LogiX xin lỗi vì trải nghiệm chưa tốt, mong anh/chị thông cảm và tiếp tục ủng hộ LogiX. | PASS | FAIL | Đồng ý nhãn human theo rubric: ledger ghi 35.000đ | Rubric helpful: bắt buộc đúng số tiền/trạng thái, trả lời trực tiếp hoặc hỏi đúng thông tin thiếu; lời xin lỗi không đủ. |
| HL-020 | Dạ, LogiX đã hoàn 90.000đ cho đơn O-303 ạ. | PASS | FAIL | Đồng ý nhãn human theo rubric: ledger ghi 120.000đ | Rubric helpful: bắt buộc đúng số tiền/trạng thái, trả lời trực tiếp hoặc hỏi đúng thông tin thiếu; lời xin lỗi không đủ. |
| HL-028 | Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. LogiX đã hoàn 50.000đ cho đơn O-677. LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. | PASS | FAIL | Đồng ý nhãn human theo rubric: ledger ghi 35.000đ | Rubric helpful: bắt buộc đúng số tiền/trạng thái, trả lời trực tiếp hoặc hỏi đúng thông tin thiếu; lời xin lỗi không đủ. |
| HL-035 | Dạ, Một lần nữa LogiX xin lỗi vì trải nghiệm chưa tốt, mong anh/chị thông cảm và tiếp tục ủng hộ LogiX. LogiX đã hoàn 50.000đ cho đơn O-303. LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. | PASS | FAIL | Đồng ý nhãn human theo rubric: ledger ghi 35.000đ | Rubric helpful: bắt buộc đúng số tiền/trạng thái, trả lời trực tiếp hoặc hỏi đúng thông tin thiếu; lời xin lỗi không đủ. |

`helpful` bỏ sót 21/30 lỗi: recall=0.3 và κ=0.375 không đạt, dù precision=1.0. Không đưa tiêu chí này vào gate.
`tone_ok` đạt floors nhưng không phải bảo đảm cho mọi dữ liệu; hiện chỉ là judge đủ chuẩn trên replay, chưa nối vào gate tiền.
Rogan–Gladen sửa ước lượng tỉ lệ tổng thể, không sửa nhãn từng case và không làm helpful đạt chuẩn.
Cần rubric mới và nhãn held-out mới để kiểm tra lại; không tuyên bố đã cải thiện judge chỉ bằng sửa văn bản rubric.
