# TÀI LIỆU YÊU CẦU NGHIỆP VỤ (BRD)

## Hệ thống hỗ trợ chăm sóc khách hàng cho đơn hàng và sản phẩm có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 4.2 |
| Trạng thái | Bản nháp để nhóm review |
| Ngày | 21/10/2026 |
| Tài liệu liên quan | FRD_olist_hidden_dissatisfaction.md (v2.2); API_CONTRACT_olist_hidden_dissatisfaction.md (v0.5); DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md (v0.5); ERD – TBD |

## 1. Tóm tắt nghiệp vụ

Một số đơn hàng Olist được giao đúng hoặc sớm hơn ngày dự kiến nhưng vẫn nhận đánh giá 1–2 sao. Nếu chỉ theo dõi đơn giao trễ, doanh nghiệp có thể bỏ sót nhóm khách hàng bất mãn này.

Hệ thống hỗ trợ đội ngũ chăm sóc khách hàng và Manager ưu tiên kiểm tra, theo dõi và điều phối case. Mô hình học máy tạo risk score và các yếu tố liên quan cho từng sản phẩm trong đơn hàng, sau đó tạo kết quả tổng hợp cho đơn hàng. Kết quả chỉ dùng để ưu tiên nhân viên kiểm tra; không phải kết luận nguyên nhân, không tự động liên hệ khách hàng và không tự động quyết định hoàn tiền hay bồi thường.

Olist chỉ có review ở cấp đơn. Trong phiên bản hiện tại, mỗi product item kế thừa nhãn review của đơn chứa nó. Điểm item biểu thị rủi ro review thấp của đơn trong bối cảnh item đó, không chứng minh item gây bất mãn. Điểm order được tổng hợp theo `max-v1` (điểm item cao nhất trong đơn); mọi thay đổi quy tắc phải tạo version mới.

## 2. Vấn đề và mục tiêu

### 2.1. Vấn đề hiện tại

- Nhân viên thường phải chọn thủ công đơn cần kiểm tra.
- Đơn giao đúng hạn thường bị xem là ít rủi ro.
- Không có cách thống nhất để ưu tiên theo mức độ rủi ro và nguồn lực hiện có.
- Manager khó biết nhóm đang tồn bao nhiêu đơn, ai đang giữ đơn nào và rủi ro tập trung ở seller/ngành hàng nào.
- Một đơn hàng có thể gồm nhiều sản phẩm; chỉ xem kết quả chung của đơn làm CSKH khó biết sản phẩm nào cần kiểm tra trước.
- Một phần dữ liệu chưa có đủ chi tiết sản phẩm để tạo output theo từng sản phẩm.

### 2.2. Mục tiêu

1. Tạo danh sách đơn giao đúng hạn được xếp hạng theo risk score tổng hợp.
2. Giúp Specialist biết nên bắt đầu xử lý đơn nào và sản phẩm nào trong đơn cần kiểm tra.
3. Giúp Manager theo dõi toàn bộ tiến độ, phân bổ nguồn lực và chuyển đổi giữa góc nhìn đơn hàng và sản phẩm.
4. Cho phép Manager tự cấu hình các tham số vận hành mà không cần thay đổi code.
5. Chuẩn hóa trạng thái, kết quả xử lý, lần liên lạc và quyết định quản lý ở cấp case đơn hàng.
6. Lưu lịch sử để biết ai đã thao tác, thao tác gì và tại thời điểm nào.

### 2.3. Không phải mục tiêu

- Chứng minh nguyên nhân khách hàng không hài lòng.
- Tự động liên hệ khách hàng.
- Tự động thay đổi risk score.
- Đánh giá hiệu quả của từng biện pháp chăm sóc.
- Dự đoán khách hàng quay lại hoặc customer retention.

## 3. Persona

### 3.1. Persona 1: Customer Service Specialist

**Tên đại diện:** Linh  
**Vai trò:** Nhân viên chăm sóc khách hàng trực tiếp xử lý các đơn được hệ thống ưu tiên.

**Bối cảnh làm việc:**

- Có số lượng đơn cần xử lý giới hạn trong mỗi ca.
- Không thể xem thủ công toàn bộ đơn hàng.
- Cần biết đơn nào nên xử lý trước.
- Có thể phải liên lạc nhiều lần với cùng một khách hàng.

**Mục tiêu:**

- Nhận đúng các đơn có mức ưu tiên cao.
- Hiểu vì sao đơn bị đánh dấu rủi ro.
- Cập nhật trạng thái và kết quả xử lý nhanh.
- Không vượt quá số đơn đang giữ cùng lúc.

**Pain point:**

- Danh sách thủ công không phản ánh mức độ rủi ro.
- Không biết đơn nào chưa có người xử lý.
- Dễ quên các đơn cần liên lạc lại.
- Khó phân biệt đơn đã xử lý với đơn chỉ mới được xem.

**Thông tin cần xem:**

- Order ID, risk score, risk level.
- Seller, ngành hàng, thời gian giao hàng.
- Yếu tố liên quan đến risk score.
- Trạng thái, người phụ trách, thời hạn xử lý.
- Lịch sử liên lạc và ghi chú.

**Quyền và giới hạn:**

- Được xem Risk Queue, Order Detail, tìm kiếm và lọc.
- Được tự nhận LOW/MEDIUM-risk case nếu còn capacity; không được tự nhận HIGH-risk case.
- Được cập nhật trạng thái và outcome của đơn mình xử lý.
- Không được assign/reassign cho người khác.
- Không được sửa risk score gốc.
- Không có Risk Overview Dashboard riêng trong MVP.

**Tiêu chí thành công:**

- Nhìn vào Risk Queue có thể biết nên bắt đầu từ đơn nào.
- Nhận đơn không vượt capacity đang có hiệu lực.
- Hoàn tất một đơn mà không thiếu thông tin bắt buộc.

### 3.2. Persona 2: Supervisor/Manager

**Tên đại diện:** Minh  
**Vai trò:** Quản lý nhóm chăm sóc khách hàng và quyết định phân bổ nguồn lực.

**Bối cảnh làm việc:**

- Chịu trách nhiệm về tiến độ và số lượng đơn tồn.
- Cần biết rủi ro tập trung ở seller/ngành hàng nào.
- Cần nhìn workload của từng Specialist.
- Có thể phải can thiệp khi đơn bị treo hoặc được phân công sai.

**Mục tiêu:**

- Theo dõi tổng quan số lượng và phân bố đơn rủi ro.
- Biết nhóm đã xử lý bao nhiêu và còn tồn bao nhiêu.
- Phân bổ lại đơn khi cần.
- Kiểm soát các trường hợp quá SLA.
- Có thể mở lại hoặc override workflow trong trường hợp hợp lý.

**Pain point:**

- Không có cái nhìn tổng thể về tiến độ nhóm.
- Không biết Specialist nào đang quá tải.
- Không biết HIGH-risk orders đang tập trung ở đâu.
- Khó truy lại lý do một đơn bị đổi người hoặc đổi trạng thái.

**Thông tin cần xem:**

- Tổng số risk orders theo thời gian và risk level.
- HIGH orders chưa xử lý.
- Số đơn quá SLA.
- Tỷ lệ hoàn thành, bỏ qua và không liên lạc được.
- Phân bố theo seller/ngành hàng.
- Số đơn đang giữ của từng Specialist.
- Lịch sử override và phân công.

**Quyền và giới hạn:**

- Được xem Risk Overview Dashboard, Risk Queue và Order Detail.
- Được assign/reassign.
- Được mở lại case đã hoàn tất hoặc bỏ qua.
- Được override workflow và capacity khi cần.
- Được quản lý Parameter Configuration và chọn ngôn ngữ giao diện.
- Mọi override bắt buộc ghi lý do.
- Không được sửa risk score/model output gốc trong MVP.

**Tiêu chí thành công:**

- Có thể phát hiện nhóm đơn tồn hoặc quá SLA.
- Có thể biết Specialist nào còn capacity.
- Có thể điều phối lại đơn và truy vết được lịch sử.

## 4. Phạm vi sản phẩm

### 4.1. Trong phạm vi

- Risk Overview Dashboard cho Manager, có chế độ xem theo đơn hàng hoặc sản phẩm.
- Dashboard có biểu đồ xu hướng số case đi vào Risk Queue theo ngày, tách màu LOW/MEDIUM/HIGH và chạy theo bộ lọc đang áp dụng.
- Risk Queue dùng chung cho Specialist và Manager, hiển thị tín hiệu rủi ro sản phẩm quan trọng nhất của đơn.
- Order Detail là hồ sơ tổng hợp, có thông tin đơn hàng, output ML, nhận xét, next step, status và liên kết đến lịch sử Attempt.
- Attempt là trang riêng để Specialist chọn case đang được giao và thêm mới từng lần liên lạc kèm minh chứng file.
- Manager Decision là trang riêng để Manager xem hồ sơ, output ML và Attempt trước khi ghi quyết định, lý do và next step.
- Tìm kiếm và lọc.
- Tự nhận đơn, assign và reassign.
- Review status, review outcome và contact activity.
- Minh chứng cho lần liên lạc, nhận xét nội bộ và quyết định/bước tiếp theo của Manager.
- SLA, aging, retry, escalation.
- Manager override và audit log.
- Parameter Configuration do Manager quản lý, gồm lịch SLA, thời lượng SLA, số lần retry, khoảng cách retry và capacity.
- Chuyển đổi ngôn ngữ giao diện tiếng Việt/tiếng Anh.
- Risk score, risk level, explanation và báo cáo ML ở cấp sản phẩm và cấp đơn hàng.
- Dữ liệu chi tiết sản phẩm giả lập có gắn cờ nguồn dữ liệu khi dữ liệu gốc thiếu, chỉ dùng cho mục đích thử nghiệm/minh họa ML.

### 4.2. Ngoài phạm vi

- Tự động liên hệ, hoàn tiền, bồi thường hoặc tặng ưu đãi.
- Sửa risk score bởi người dùng nghiệp vụ.
- Realtime integration với hệ thống thương mại điện tử.
- Tự động retrain model trong production.

## 5. Các chức năng nghiệp vụ chính

| Chức năng | Specialist | Manager | Kết quả nghiệp vụ |
|---|---:|---:|---|
| Risk Overview Dashboard | Không cần trong MVP | Có | Theo dõi tiến độ, phân bố rủi ro, xu hướng case vào Queue và workload |
| Risk Queue | Có | Có | Ưu tiên danh sách đơn; HIGH-risk case chờ Manager giao |
| Order Detail | Có | Có | Hiểu context, risk và lịch sử |
| Attempt | Thêm mới với case được giao | Chỉ xem | Ghi nhận từng lần liên lạc, minh chứng và đề xuất bước tiếp theo |
| Manager Decision | Không | Có | Ghi quyết định quản lý, lý do và next step |
| Search and Filter | Có | Có | Tìm đúng nhóm đơn |
| Review Status | Cập nhật | Xem/override | Theo dõi vòng đời xử lý |
| Assignment | Tự nhận LOW/MEDIUM | Assign/reassign; bắt buộc giao HIGH | Phân bổ nguồn lực theo risk level |
| Parameter Configuration | Không | Có | Tự cấu hình quy tắc vận hành có kiểm soát |
| Language switch | Có | Có | Dùng giao diện tiếng Việt hoặc tiếng Anh |

Risk Queue của Specialist phải có summary banner: số HIGH chưa xử lý, đơn nên bắt đầu và số slot còn lại.

Order Detail hiển thị thông tin đơn hàng, output ML, nhận xét, tóm tắt Attempt, lịch sử status và next step. Attempt chỉ được thêm mới tại trang Attempt, không sửa hoặc xóa. Decision mới nhất của Manager phải hiển thị lại tại Order Detail.

## 6. Business rules

### 6.1. Quy tắc về model output

1. Risk score do model tạo ra, không phải kết luận chắc chắn.
2. Model tạo score, level, explanation và prediction metadata cho từng sản phẩm trong đơn hàng; mỗi kết quả gắn Order ID và Product Item ID.
3. Kết quả đơn hàng là output tổng hợp từ các product-item output theo aggregation rule được version hóa; phiên bản đầu tiên là `max-v1`. Giao diện phải nêu rõ đây là kết quả tổng hợp.
4. Risk score được map thành LOW, MEDIUM hoặc HIGH; risk level, threshold và aggregation rule phải được version hóa.
5. Manager chỉ được ghi chú hoặc đánh dấu cần xem lại model; không sửa score gốc ở bất kỳ cấp nào.
6. Suggested action chỉ là đề xuất, không tự động liên hệ khách hàng.

### 6.2. Quy tắc về danh sách ưu tiên

1. Risk Queue mặc định sắp xếp risk score giảm dần.
2. Nếu cùng score, ưu tiên đơn gần quá SLA hơn.
3. Nếu vẫn giống nhau, ưu tiên đơn có thời gian nằm trong queue lâu hơn.
4. Đơn HIGH chưa xử lý phải được đưa vào summary banner.
5. Specialist chỉ thấy action mà role của mình được phép thực hiện.

### 6.3. Quy tắc về assignment và capacity

1. Specialist chỉ tự bấm Nhận xử lý với LOW/MEDIUM-risk case; HIGH-risk case phải do Manager assign/reassign.
2. Một Specialist được giữ tối đa số active orders theo Parameter Configuration đang có hiệu lực.
3. Khi đạt ngưỡng cảnh báo capacity theo Parameter Configuration, hệ thống phải hiển thị cảnh báo.
4. Khi đủ capacity đang có hiệu lực, không cho claim thêm.
5. Khi case COMPLETED hoặc SKIPPED, slot được giải phóng.
6. Manager được assign/reassign.
7. Một case chỉ có một assignee active tại một thời điểm.
8. Nếu hai người cùng claim, chỉ thao tác thành công đầu tiên được ghi nhận.
9. Manager override capacity bắt buộc ghi lý do.

### 6.4. Quy tắc về trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| PENDING | Chưa có người xử lý |
| IN_PROGRESS | Đã claim hoặc được assign |
| COMPLETED | Đã hoàn tất và có outcome |
| SKIPPED | Không tiếp tục xử lý và có lý do |

Chuyển trạng thái hợp lệ:

- PENDING → IN_PROGRESS: Specialist claim LOW/MEDIUM-risk case hoặc Manager assign; HIGH-risk case chỉ Manager được assign.
- IN_PROGRESS → COMPLETED: có outcome bắt buộc.
- IN_PROGRESS → SKIPPED: có reason bắt buộc.
- COMPLETED/SKIPPED → PENDING: chỉ Manager, có override reason.

### 6.5. Quy tắc về outcome

Khi COMPLETED, bắt buộc chọn:

- Có vấn đề.
- Không có vấn đề.
- Trùng case hoặc outcome bổ sung được Product Owner phê duyệt.

### 6.6. Quy tắc liên lạc lại

1. Mỗi Attempt là một lần liên lạc thuộc một case; phải lưu thời điểm, phương thức, kết quả, ghi chú và người ghi nhận.
2. Chỉ assignee hiện tại được thêm Attempt cho case `IN_PROGRESS`. Attempt đã ghi là append-only, không sửa hoặc xóa.
3. Attempt có thể kèm tối đa ba tệp PNG, JPG hoặc PDF, mỗi tệp tối đa 5 MB. Không nhận URL tùy ý làm minh chứng.
4. Số lần liên lạc tối đa và khoảng cách giữa hai lần được lấy từ Parameter Configuration đang có hiệu lực.
5. Sau Attempt không thành công cuối cùng theo parameter, Backend tự chuyển case sang `SKIPPED` với `skip_reason = UNREACHABLE` và tạo audit event.
6. SKIPPED bắt buộc chọn lý do.
7. Manager có thể mở lại case nếu có lý do nghiệp vụ.

### 6.7. Quy tắc SLA, aging và escalation

| Quy tắc | Giá trị ban đầu | Xử lý |
|---|---:|---|
| First-touch SLA | Theo Parameter Configuration | Cảnh báo nếu chưa nhận |
| HIGH-risk SLA | Theo Parameter Configuration | Ưu tiên/escalation |
| MEDIUM-risk SLA | Theo Parameter Configuration | Cảnh báo quá hạn |
| LOW-risk SLA | Theo Parameter Configuration | Xử lý sau |
| In-progress timeout | Theo Parameter Configuration | Cảnh báo Manager |
| Queue aging | Theo Parameter Configuration | Đưa vào escalation queue |
| Reopen review | Sau 7 ngày hoặc quá 2 lần | Manager review bắt buộc |

SLA của một review cycle được tính từ thời điểm case vào Risk Queue hoặc thời điểm reopen gần nhất đến khi case chuyển COMPLETED/SKIPPED. Báo cáo vẫn lưu `original_queue_entered_at` để tính total case aging từ lần vào Queue đầu tiên. Lịch SLA (giờ làm việc hoặc ngày lịch), thời lượng SLA, retry limit, retry interval và capacity lấy từ Parameter Configuration.

### 6.8. Quy tắc override và audit

Manager được:

- Mở lại COMPLETED hoặc SKIPPED.
- Đổi assignee.
- Override capacity hoặc workflow.

Mỗi override phải lưu actor, thời gian, action, giá trị cũ, giá trị mới và reason. Không được xóa audit history.

Khi mở lại case, Manager bắt buộc ghi lý do. Hệ thống tạo review cycle mới, reset retry counter và tính lại SLA từ thời điểm reopen; contact history và queue-entry timestamp ban đầu vẫn được giữ nguyên.

### 6.9. Quy tắc Parameter Configuration

1. Chỉ Manager được tạo, sửa hoặc kích hoạt Parameter Configuration.
2. Mỗi thay đổi phải lưu parameter key, giá trị cũ/mới, version, actor, lý do và effective timestamp.
3. Parameter mới chỉ áp dụng cho case đang mở tại thời điểm có hiệu lực và case tạo sau đó; case đã đóng giữ parameter version từng áp dụng trong history.
4. Case đang mở áp dụng giá trị mới từ effective timestamp; các giá trị đã phát sinh trong history không được ghi đè.

### 6.10. Quy tắc ngôn ngữ

1. Người dùng được chọn tiếng Việt hoặc tiếng Anh cho giao diện.
2. Việc đổi ngôn ngữ chỉ thay đổi nhãn, thông báo và nội dung hiển thị; không thay đổi mã trạng thái, score, dữ liệu gốc hoặc audit event.

### 6.11. Quy tắc minh chứng và nhận xét

1. Người đang giữ case được tải tối đa ba tệp PNG, JPG hoặc PDF, mỗi tệp tối đa 5 MB, cho một Attempt; tệp chỉ được gắn một lần và không dùng URL bên ngoài thay thế.
2. Người đang giữ case và Manager được thêm nhận xét nội bộ; nhận xét chỉ được thêm mới, không sửa hoặc xóa.
3. Upload và nhận xét phải được kiểm tra quyền; nhận xét tạo audit event.

### 6.12. Quy tắc Manager Decision

1. Chỉ Manager được tạo decision; decision không thay đổi risk score hoặc model output.
2. Trước khi quyết định, Manager phải xem được order context, output ML cấp item/order, nhận xét, lịch sử Attempt và minh chứng.
3. Mỗi decision bắt buộc có `decision`, `reason` và `next_step`; có thể có `next_step_assignee_id`, `due_date` và `note`.
4. Decision gắn với review cycle hiện tại, chỉ thêm mới, không sửa hoặc xóa; decision mới nhất hiển thị ở Order Detail.
5. Decision chỉ điều phối workflow, không tự động liên hệ, hoàn tiền hoặc bồi thường.



## 7. Tiêu chí nghiệm thu nghiệp vụ

- Đúng quyền theo role.
- Specialist không claim vượt capacity đang có hiệu lực.
- Không có hai assignee active cho cùng case.
- Thiếu outcome/reason thì không được hoàn tất/bỏ qua.
- Retry bị chặn theo retry limit đang có hiệu lực.
- Attempt chỉ do assignee hiện tại thêm mới; Attempt cũ không sửa/xóa và minh chứng tuân thủ giới hạn file.
- Hết retry không thành công tự chuyển SKIPPED với lý do `UNREACHABLE`; giá trị này không còn là COMPLETED outcome.
- Manager Decision bắt buộc có decision, reason và next step; decision mới nhất xuất hiện ở Order Detail.
- Manager override luôn có audit event.
- Risk score gốc không bị sửa.
- Dashboard và Queue dùng cùng định nghĩa status/risk/metric.
- Dashboard có biểu đồ số case vào Risk Queue theo ngày, tách màu LOW/MEDIUM/HIGH và phản ánh đúng bộ lọc.
- HIGH-risk case không thể được Specialist tự claim; Manager assign/reassign và có audit event.
- Parameter chỉ Manager được sửa, có version/effective time/audit; case đóng giữ lịch sử parameter, case mở áp dụng parameter mới từ lúc hiệu lực.
- Reopen reset retry counter và current-cycle SLA, nhưng giữ contact history và original queue-entry timestamp.
- Người dùng chuyển được tiếng Việt/tiếng Anh mà không làm thay đổi dữ liệu nghiệp vụ.
- Manager xem được output ML ở cấp đơn hàng và từng sản phẩm, đồng thời chuyển đổi chế độ xem mà không làm thay đổi dữ liệu gốc.
- Output sản phẩm truy vết được về Order ID, Product Item ID, model version và nguồn dữ liệu; output đơn hàng truy vết được về aggregation rule.
- Báo cáo có leakage audit, temporal evaluation và calibration.
- Temporal split và bootstrap thực hiện theo `order_id`; mọi item của cùng một đơn phải nằm trong cùng một partition.
- Minh chứng và nhận xét tuân thủ quyền, giới hạn tệp và quy tắc audit tại mục 6.11; decision tuân thủ mục 6.12.

## 9. Trình tự bàn giao

BRD → FRD → ERD → API Document → thiết kế giao diện → triển khai và kiểm thử.
