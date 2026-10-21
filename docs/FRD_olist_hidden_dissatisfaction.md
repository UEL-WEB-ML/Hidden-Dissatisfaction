# TÀI LIỆU YÊU CẦU CHỨC NĂNG (FRD)

## Hệ thống hỗ trợ chăm sóc khách hàng cho đơn hàng và sản phẩm có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 2.2 |
| Trạng thái | Bản nháp để nhóm review |
| Ngày | 21/10/2026 |
| Tài liệu liên quan | BRD_olist_hidden_dissatisfaction.md (v4.2); API_CONTRACT_olist_hidden_dissatisfaction.md (v0.5); DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md (v0.5); ERD – TBD |

## 1. Mục đích và nguyên tắc

FRD chuyển yêu cầu nghiệp vụ thành function, sub-function, hành vi giao diện, dữ liệu, dependency, validation và tiêu chí nghiệm thu. Hệ thống hỗ trợ CSKH ở hai cấp: case đơn hàng để quản lý workflow và product item để xem output ML chi tiết; output đơn hàng là kết quả tổng hợp từ các output sản phẩm. Cấu trúc này được thiết kế để có thể tách trực tiếp thành Jira task cho Frontend.

FRD chưa chốt tên bảng ERD, endpoint API, request/response cụ thể hoặc thiết kế pixel.

## 2. Summary Function Catalogue

| Mã function | Function | Mục đích | Actor chính | Dependency chính | Ưu tiên |
|---|---|---|---|---|---|
| F01 | Risk Overview Dashboard | Giúp Manager theo dõi theo đơn hàng hoặc sản phẩm và phân bổ nguồn lực | Manager | Metric definition, dữ liệu tổng hợp, quyền Manager | Must |
| F02 | Risk Queue | Giúp Specialist/Manager xem và ưu tiên các đơn rủi ro có tín hiệu sản phẩm | Specialist, Manager | Order Risk Case, product-item risk output, status, assignment | Must |
| F03 | Search and Filter | Giúp tìm đúng đơn hoặc nhóm đơn cần xem | Specialist, Manager | Filter fields, queue query, quyền dữ liệu | Must |
| F04 | Order Detail | Cung cấp context, output tổng hợp và output theo từng sản phẩm của một đơn | Specialist, Manager | Order data, product-item output, aggregation, activity, audit | Must |
| F05 | Claim and Assignment | Gán trách nhiệm xử lý và kiểm soát capacity | Specialist, Manager | User/role, capacity, assignment state, concurrency | Must |
| F06 | Review Status and Outcome | Chuẩn hóa kết quả xử lý của Specialist | Specialist, Manager | State machine, outcome catalogue, validation | Must |
| F07 | Attempt, Contact Retry and Escalation | Thêm từng lần liên lạc tại trang riêng, theo dõi retry, SLA và case quá hạn | Specialist, Manager | Contact activity, evidence, threshold, business calendar | Should |
| F08 | Manager Override | Cho Manager can thiệp workflow có kiểm soát | Manager | Permission, reason, audit event | Must |
| F09 | Audit History | Truy vết mọi thay đổi quan trọng | Manager, người được cấp quyền | Audit event, read permission | Must |
| F10 | Parameter Configuration | Cho Manager cấu hình quy tắc vận hành có kiểm soát | Manager | Parameter version, effective time, audit event | Must |
| F11 | Language Switch | Cho người dùng chọn giao diện tiếng Việt hoặc tiếng Anh | Specialist, Manager | Translation catalogue, user preference | Should |
| F12 | Manager Decision | Cho Manager ghi quyết định và next step sau khi xem hồ sơ case | Manager | Order detail, ML output, Attempt, permission, audit | Must |

## 3. Actor và phân quyền

| Chức năng | Specialist | Manager |
|---|---:|---:|
| Xem Risk Queue | Có | Có |
| Xem Order Detail | Có | Có |
| Thêm Attempt | Chỉ case `IN_PROGRESS` đang được giao | Không |
| Xem minh chứng Attempt | Có, trong case được giao | Có |
| Ghi Manager Decision | Không | Có |
| Tìm kiếm/lọc | Có | Có |
| Xem Risk Overview Dashboard | Không trong MVP | Có |
| Nhận xử lý | Chỉ LOW/MEDIUM | Có thể assign mọi risk level |
| Assign/reassign | Không | Có |
| Cập nhật status/outcome | Có | Có |
| Override status/assignee | Không | Có |
| Sửa risk score/model output | Không | Không |
| Quản lý Parameter Configuration | Không | Có |
| Chọn ngôn ngữ giao diện | Có | Có |

Frontend ẩn hoặc disable action ngoài quyền; Backend vẫn kiểm tra quyền độc lập.

## 4. Logical data và trạng thái dùng chung

### 4.1. Logical data object

| Object | Mục đích |
|---|---|
| Order Risk Case | Order context, score, level, ranking, prediction metadata |
| Product Item Risk Output | Product Item ID, thuộc tính sản phẩm, score, level, explanation, model version, timestamp, nguồn dữ liệu |
| Order Risk Aggregation | Output tổng hợp của đơn, aggregation rule/version và liên kết tới product-item output |
| Review Assignment | Assignee hiện tại và lịch sử phân công |
| Review Status | Trạng thái xử lý hiện tại |
| Review Activity / Attempt | Lần liên lạc append-only, ghi chú và next contact |
| Contact Evidence | Tệp PNG/JPG/PDF gắn với một Attempt; không nhận URL tùy ý |
| Case Comment | Nhận xét nội bộ chỉ thêm mới của người giữ case hoặc Manager |
| Manager Decision | Quyết định, lý do, next step, người thực hiện tùy chọn, hạn xử lý, actor và thời điểm |
| Review Outcome | Kết quả khi hoàn tất |
| Audit Event | Lịch sử override và thay đổi |
| User/Role | Người dùng và quyền |
| Threshold Configuration | Capacity, SLA, retry, escalation |
| Parameter Configuration | Giá trị cấu hình, version, effective timestamp, trạng thái, actor, reason và lịch sử thay đổi |
| Review Cycle | Mốc bắt đầu/kết thúc SLA, retry counter và parameter version áp dụng cho một lần xử lý case |

Order Risk Case là đơn vị workflow, assignment, status, Attempt và Manager Decision. Product Item Risk Output là đơn vị ML; một case có một hoặc nhiều output sản phẩm. Mỗi Attempt thuộc một case/review cycle, do assignee hiện tại thêm và không được sửa/xóa. Mỗi case lưu `original_queue_entered_at`; mỗi Review Cycle lưu SLA start/end, retry counter và parameter version. Với product item giả lập do thiếu dữ liệu gốc, `synthetic_data_flag` phải được trả về để giao diện gắn nhãn rõ ràng.

Review Olist tồn tại ở cấp order. Mọi product item của một order kế thừa cùng nhãn huấn luyện; item score là rủi ro review thấp của order trong bối cảnh item, không phải kết luận item gây bất mãn. Order Risk Aggregation v1 dùng `max-v1`. Temporal split, bootstrap và kiểm tra leakage phải group theo `order_id`.

### 4.2. Review status

PENDING → IN_PROGRESS → COMPLETED hoặc SKIPPED.

- COMPLETED bắt buộc có outcome.
- SKIPPED bắt buộc có reason.
- COMPLETED/SKIPPED → PENDING chỉ dành cho Manager và bắt buộc override reason.
=

## 5. F01 – Risk Overview Dashboard

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F01-S01 Bộ lọc Dashboard | Xem đúng phạm vi dữ liệu | Manager | Quyền Manager; định nghĩa filter; dữ liệu Dashboard | Lọc thời gian, risk level, seller, ngành hàng, Specialist, status, Product Item ID; có Áp dụng/Đặt lại | Filter đang dùng được hiển thị; reset đưa về mặc định |
| F01-S02 Chế độ xem | Chuyển giữa góc nhìn nghiệp vụ | Manager | View state; metric definition; dữ liệu Dashboard | Có lựa chọn Order view và Product view; khi đổi view giữ các filter còn tương thích | View đang chọn hiển thị rõ; số liệu và danh sách dùng đúng grain |
| F01-S03 Thẻ chỉ số | Nắm nhanh khối lượng và tiến độ | Manager | Metric definition; dữ liệu tổng hợp | Order view hiển thị tổng risk orders, HIGH chưa xử lý, IN_PROGRESS, COMPLETED, SKIPPED, quá SLA; Product view hiển thị tổng risk product items và phân bố level | Số liệu đồng nhất theo view và filter; có loading/error |
| F01-S04 Phân bố risk | Biết rủi ro tập trung ở đâu | Manager | Risk score/level; threshold version | Hiển thị LOW/MEDIUM/HIGH và score bands theo grain đang chọn | Tổng nhóm khớp tổng bản ghi trong view |
| F01-S05 Seller/ngành hàng | Phát hiện nguồn tập trung rủi ro | Manager | Seller/category aggregation | Hiển thị nhóm có nhiều HIGH hoặc đơn tồn; Product view cho phép xem theo sản phẩm/ngành hàng | Có empty state; drill-down nếu được hỗ trợ |
| F01-S06 Workload Specialist | Quyết định phân bổ nguồn lực | Manager | User/role; active count; Parameter Configuration | Hiển thị active orders, đơn quá hạn, slot còn lại từng Specialist | Slot không âm; dùng đúng capacity đang có hiệu lực |
| F01-S07 Drill-down | Đi từ tổng quan đến case cụ thể | Manager | Filter state; F02 Risk Queue; F04 Order Detail | Bấm metric mở Queue với filter tương ứng; từ Product view có thể mở order và focus product item | Queue/Detail nhận đúng filter và product item context |
| F01-S08 Xu hướng Risk Queue | Theo dõi số case vào Queue theo thời gian | Manager | Queue entry timestamp; risk level; filter state | Biểu đồ theo ngày, mỗi LOW/MEDIUM/HIGH một màu; chạy theo bộ lọc Dashboard | Tổng theo ngày và risk level khớp số case vào Queue trong phạm vi filter |

## 6. F02 – Risk Queue

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F02-S01 Summary banner | Giúp Specialist biết nên bắt đầu từ đâu | Specialist | Queue data; current user; capacity | Hiển thị HIGH chưa xử lý, đơn đề xuất đầu tiên, active/capacity, slot còn lại | Banner cập nhật sau claim, complete, skip, reassign |
| F02-S02 Danh sách risk orders | Xem và so sánh case | Specialist/Manager | Order Risk Case; Product Item Risk Output; permission scope; pagination | Cột: Order ID, score/level tổng hợp, sản phẩm cần kiểm tra, mức rủi ro sản phẩm, seller/ngành hàng, aging, SLA, status, assignee, action | Dữ liệu đúng và action đúng role; một đơn vẫn chỉ xuất hiện một dòng queue |
| F02-S03 Sắp xếp ưu tiên | Đưa case cần xử lý lên trước | Specialist/Manager | Risk score; SLA; aging | Mặc định score giảm dần; tie-breaker là SLA rồi aging | Thứ tự ổn định; có chỉ báo sort |
| F02-S04 Action theo role/state | Tránh thao tác sai | Specialist/Manager | Permission; risk level; state transition | Specialist chỉ thấy Nhận xử lý với LOW/MEDIUM; HIGH hiển thị chờ Manager giao; Manager thấy Assign/Reassign | Không hiện action trái quyền/sai state |
| F02-S05 Tải thêm | Xem queue lớn không mất trạng thái | Specialist/Manager | Pagination/load-more contract | Tải tiếp theo, giữ filter/sort, không trùng dòng | Loading tải thêm rõ ràng; không mất dữ liệu |

## 7. F03 – Search and Filter

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F03-S01 Tìm Order ID hoặc Product Item ID | Mở nhanh một đơn hoặc sản phẩm cụ thể | Specialist/Manager | ID validation; search result | Ô nhập, đang tìm, not found, invalid format; tìm theo Product Item ID mở Order Detail và focus item | Kết quả đúng hoặc thông báo phù hợp |
| F03-S02 Lọc theo risk | Thu hẹp theo mức độ rủi ro | Specialist/Manager | Risk band; score range | Lọc LOW/MEDIUM/HIGH hoặc score range | Kết quả đúng; giữ filter khi refresh |
| F03-S03 Lọc theo nghiệp vụ | Tìm theo context vận hành | Specialist/Manager | Seller, category, date, status, outcome, assignee | Cho phép chọn một hoặc nhiều điều kiện | Các filter kết hợp được |
| F03-S04 Hiển thị filter state | Biết truy vấn hiện tại | Specialist/Manager | Filter state | Hiển thị chip/summary, xóa từng filter | Người dùng biết filter nào đang áp dụng |
| F03-S05 Reset filter | Trở về danh sách mặc định | Specialist/Manager | Default query | Xóa toàn bộ filter và tải lại queue | Kết quả về đúng mặc định |

## 8. F04 – Order Detail

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F04-S01 Order context | Hiểu thông tin nền của đơn | Specialist/Manager | Order data; prediction-time rule | Hiển thị Order ID, seller, ngành hàng, giao hàng và field được phép | Không hiển thị field phát sinh sau mốc dự báo nếu bị cấm |
| F04-S02 Order-level risk output | Hiểu kết quả tổng hợp của đơn | Specialist/Manager | Order Risk Aggregation; metadata | Hiển thị score, level, suggested action, aggregation rule/version, model version, timestamp và disclaimer | Có đủ metadata; nêu rõ là output tổng hợp từ sản phẩm |
| F04-S03 Danh sách product item | Xem output ML từng sản phẩm trong đơn | Specialist/Manager | Product Item Risk Output; sort; synthetic flag | Hiển thị Product Item ID, tên/thuộc tính cho phép, score, level, suggested action, model version, timestamp, source flag; cho phép sort theo score và focus item | Mỗi item liên kết đúng Order ID; item giả lập có nhãn rõ ràng |
| F04-S04 Product-item explanation | Hiểu yếu tố liên quan đến score của sản phẩm | Specialist/Manager | Explanation output; wording guideline | Chọn một product item để hiển thị top factors; không gọi là causal reason | Thiếu explanation có trạng thái rõ |
| F04-S05 Status/assignment | Biết ai đang xử lý và case ở đâu | Specialist/Manager | Status; assignment; SLA | Hiển thị status, outcome, assignee, aging, SLA | Khớp dữ liệu Queue |
| F04-S06 Attempt, nhận xét và decision summary | Xem diễn biến xử lý mà không thao tác nhầm nơi | Specialist/Manager | Attempt, Case Comment, Manager Decision; permission | Hiển thị tóm tắt Attempt, minh chứng, next contact, nhận xét và decision mới nhất; liên kết sang trang tương ứng | Timeline đúng thời gian; không có form sửa Attempt tại Order Detail |
| F04-S07 Status/next step | Biết trạng thái và việc cần làm tiếp theo | Specialist/Manager | Status, assignment, Manager Decision, SLA | Hiển thị status, outcome, assignee, aging, SLA, next step và status history | Khớp Queue; next step nhất quán với decision mới nhất |
| F04-S08 Action detail | Thực hiện action đúng quyền | Specialist/Manager | Permission; transition; capacity | Nhận, bỏ qua, hoàn tất, assign, reassign, mở lại theo state | Chỉ hiện action hợp lệ; reopen bắt buộc reason |

## 9. F05 – Claim and Assignment

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F05-S01 Specialist claim | Gán LOW/MEDIUM-risk case cho người đang đăng nhập | Specialist | Current user; PENDING; LOW/MEDIUM; claim contract | Bấm Nhận xử lý; xác nhận thành công chuyển IN_PROGRESS | HIGH không có action claim; claim hợp lệ có assignment event và cập nhật Queue/Detail |
| F05-S02 Kiểm tra capacity | Ngăn giữ quá capacity đang có hiệu lực | Specialist | Active count; Parameter Configuration | Hiển thị active/capacity; disable hoặc từ chối khi đủ | Không claim được case vượt capacity đang có hiệu lực |
| F05-S03 Concurrent claim | Tránh hai người cùng giữ case | Specialist | Concurrency contract; reload | Nếu conflict, thông báo và tải case mới | Không có hai active assignee |
| F05-S04 Manager assign | Giao case cho Specialist | Manager | User list; capacity; risk level; assignment rule | Chọn Specialist, xem capacity, xác nhận; HIGH bắt buộc đi qua action này | Case có assignee mới, status đúng và audit event |
| F05-S05 Manager reassign | Điều phối lại case | Manager | Assignee cũ/mới; reason; audit | Chọn người mới, nhập lý do, xác nhận | Hiển thị cũ/mới; audit được tạo |

## 10. F06 – Review Status and Outcome

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F06-S01 Hiển thị status | Biết vòng đời case | Specialist/Manager | Status catalogue; label mapping | Hiển thị PENDING, IN_PROGRESS, COMPLETED, SKIPPED bằng nhãn tiếng Việt | Nhãn nhất quán Queue/Detail |
| F06-S02 Hoàn tất | Ghi nhận kết quả kiểm tra | Specialist/Manager | Outcome catalogue; required fields | Form bắt buộc chọn Có vấn đề, Không có vấn đề hoặc outcome được duyệt; không có `UNREACHABLE` | Thiếu outcome không cho lưu |
| F06-S03 Bỏ qua | Đóng case có kiểm soát | Specialist/Manager | Skip reason catalogue; note rule | Chọn reason code; nhập ghi chú nếu cần | Thiếu reason không cho lưu |
| F06-S04 Kiểm tra transition | Ngăn workflow không hợp lệ | Specialist/Manager | State machine; Backend validation | Chỉ hiển thị transition hợp lệ; lỗi Backend hiển thị rõ | State sai không làm đổi dữ liệu |

## 11. F07 – Attempt, Contact Retry and Escalation

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F07-S01 Chọn case | Chỉ thêm Attempt cho đúng case được giao | Specialist | Current user; assignment; status | Hiển thị case `IN_PROGRESS` được giao cho người đăng nhập | Không thao tác được trên case khác hoặc case đã đóng |
| F07-S02 Thêm Attempt | Lưu một lần liên lạc append-only | Specialist | Attempt fields; current case | Nhập thời điểm, phương thức, kết quả, ghi chú và next contact | Gắn đúng case/cycle/actor; Attempt cũ không có action sửa/xóa |
| F07-S03 Minh chứng liên hệ | Lưu file cho một Attempt | Specialist | File upload contract; permission | Upload tối đa 3 file PNG/JPG/PDF, mỗi file tối đa 5 MB; không nhận URL tùy ý | File hợp lệ, chỉ gắn một Attempt và truy vết được |
| F07-S04 Bộ đếm retry | Biết đã thử bao nhiêu lần | Specialist/Manager | Review Cycle; Parameter Configuration | Hiển thị retry đã dùng trên retry limit | Đúng current cycle và parameter version |
| F07-S05 Hẹn liên lạc lại | Không quên lần tiếp theo | Specialist | Parameter Configuration; business calendar | Đề xuất ngày tiếp theo theo retry interval | Ngày đúng lịch cấu hình |
| F07-S06 Chặn vượt limit và tự đóng | Tuân thủ retry threshold | Specialist | Parameter Configuration; transition rule | Sau Attempt không thành công cuối cùng, Backend tự chuyển `SKIPPED/UNREACHABLE`; không cho thêm Attempt | Không vượt retry; transition và audit được tạo nguyên tử |
| F07-S07 Hiển thị SLA/escalation | Ưu tiên case sắp/quá hạn | Specialist/Manager | Review Cycle; Parameter Configuration; timezone; clock | Hiển thị SLA current cycle và total aging | Nhất quán với parameter version |

## 12. F08 – Manager Override

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F08-S01 Mở lại case | Cho xử lý lại case đã đóng | Manager | Override permission; reason; audit; Review Cycle; Parameter Configuration | COMPLETED/SKIPPED về PENDING; bắt buộc reason; tạo review cycle mới, reset retry counter và SLA từ thời điểm reopen | Có audit event; giữ contact history và original queue-entry timestamp |
| F08-S02 Đổi assignee | Chuyển trách nhiệm | Manager | User/capacity; assignment history | Hiển thị người cũ/mới; nhập reason | Cập nhật Queue/Detail và history |
| F08-S03 Ngoại lệ workflow/capacity | Cho phép xử lý tình huống đặc biệt | Manager | Warning; override rule; audit | Hiển thị cảnh báo và xác nhận bắt buộc | Không override im lặng |
| F08-S04 Khóa risk score | Bảo toàn model output gốc | Specialist/Manager | Model output permission | Không có control sửa score/level; chỉ có ghi chú model review | Score gốc không bị thay đổi |
| F08-S05 Nhận xét nội bộ | Trao đổi có truy vết trên case | Người giữ case/Manager | Case Comment; permission; audit | Thêm nhận xét tối đa 1.000 ký tự; không sửa/xóa | Nhận xét đúng actor/time và tạo audit event |

## 13. F09 – Audit History

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F09-S01 Timeline lịch sử | Biết ai làm gì, khi nào | Manager/authorized user | Audit event; read permission | Hiển thị actor, thời gian, action, old/new value, reason | Sắp xếp thời gian đúng |
| F09-S02 Phân loại event | Đọc và lọc lịch sử nhanh | Manager/authorized user | Action type catalogue | Phân biệt status, assignment, retry, skip, reopen, override, parameter change | Event type hiển thị rõ |
| F09-S03 Chỉ đọc | Bảo vệ tính toàn vẹn lịch sử | Manager/authorized user | Read-only permission | Không có sửa/xóa | Không có control thay đổi audit |

## 14. F10 – Parameter Configuration

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F10-S01 Danh sách parameter | Xem cấu hình đang có hiệu lực | Manager | Parameter Configuration; read permission | Hiển thị parameter key, giá trị, đơn vị, version, effective timestamp, trạng thái và mô tả | Có thể phân biệt bản đang hiệu lực với lịch sử |
| F10-S02 Tạo/sửa parameter | Điều chỉnh quy tắc vận hành | Manager | Validation rule; timezone; audit | Cho tạo/sửa lịch SLA, SLA theo risk level, retry limit, retry interval, capacity; bắt buộc nhập effective timestamp và reason | Giá trị/đơn vị hợp lệ; không có thay đổi không rõ thời điểm hiệu lực |
| F10-S03 Kích hoạt và áp dụng | Áp dụng cấu hình có kiểm soát | Manager | Effective-time rule; Review Cycle; case state | Khi đến effective timestamp, parameter áp dụng cho case đang mở và case tạo sau; case đóng không bị thay đổi history | Case mở dùng giá trị mới từ thời điểm hiệu lực; history đã phát sinh giữ nguyên |
| F10-S04 Lịch sử parameter | Truy vết thay đổi cấu hình | Manager | Version history; Audit Event | Xem giá trị cũ/mới, version, actor, reason và thời gian hiệu lực | Không sửa/xóa được lịch sử |

## 15. F11 – Language Switch

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F11-S01 Chọn ngôn ngữ | Dùng giao diện theo ngôn ngữ mong muốn | Specialist/Manager | User preference; translation catalogue | Có switch tiếng Việt/English ở vị trí dùng chung; lựa chọn được lưu theo user | Khi tải lại vẫn dùng lựa chọn đã lưu |
| F11-S02 Áp dụng bản dịch | Hiển thị nhất quán nội dung giao diện | Specialist/Manager | Translation catalogue | Dịch nhãn, menu, button, validation, empty/error state và nhãn trạng thái hiển thị | Không còn chuỗi giao diện sai ngôn ngữ trong các màn hình MVP |
| F11-S03 Bảo toàn dữ liệu | Không thay đổi dữ liệu nghiệp vụ khi đổi ngôn ngữ | Specialist/Manager | Status code; model output; Audit Event | Mã status, score, ID, parameter value và audit event gốc không đổi; chỉ bản hiển thị được dịch | Đổi ngôn ngữ không tạo event thay đổi nghiệp vụ |

## 16. F12 – Manager Decision

| Mã sub-function | Mục đích | Actor | Dependency | Hành vi chức năng và giao diện | Acceptance criteria |
|---|---|---|---|---|---|
| F12-S01 Danh sách case cần quyết định | Chọn đúng case để Manager xem xét | Manager | Order Risk Case; permission; filter | Hiển thị/tìm case, status, assignee, risk level, next step và decision mới nhất | Chỉ Manager truy cập; mở đúng case |
| F12-S02 Hồ sơ ra quyết định | Có đủ căn cứ trước khi quyết định | Manager | Order Detail, ML output, Attempt, evidence | Hiển thị context, output ML item/order, nhận xét, Attempt và file minh chứng | Dữ liệu cùng case; model output chỉ đọc |
| F12-S03 Ghi decision và next step | Lưu chỉ đạo quản lý có thể thực hiện | Manager | Decision fields; user list; SLA; audit | Nhập decision, reason, next step; tùy chọn người thực hiện, due date và note | Thiếu decision/reason/next step không lưu; tạo audit event |
| F12-S04 Lịch sử decision | Truy vết quyết định theo review cycle | Manager | Manager Decision; audit | Hiển thị append-only theo thời gian; đánh dấu decision mới nhất | Không sửa/xóa; summary ở Order Detail nhất quán |

## 17. Phân rã theo Epic

| Epic | Nhóm task Frontend |
|---|---|
| Dashboard | Bộ lọc; thẻ chỉ số; biểu đồ risk; seller/ngành hàng; workload; drill-down |
| Risk Queue | Banner; danh sách; badge; sort; action; tải thêm; empty/error/conflict |
| Search/Filter | Tìm Order ID; lọc risk; lọc nghiệp vụ; chip; reset |
| Order Detail | Context; risk output; explanation; assignment; Attempt/decision summary; status history; action |
| Claim/Assignment | Claim; capacity; assign; reassign; conflict |
| Review | Status selector; complete form; skip form; validation; success/error |
| Attempt/Retry/SLA | Chọn case; thêm Attempt; file evidence; retry counter; next contact; SLA; auto-skip |
| Override | Reopen; đổi assignee; xác nhận; reason |
| Audit | Timeline; event type; read-only state |
| Parameter Configuration | Danh sách; tạo/sửa; validation; effective time; version history |
| Language | Switch; user preference; bản dịch giao diện; fallback |
| Manager Decision | Danh sách case; hồ sơ; decision/reason/next step; người thực hiện; lịch sử |

## 18. Handoff sang ERD và API Document

ERD quyết định entity, table, key, relationship và cách lưu current state/history. API Document quyết định endpoint, method, request/response, pagination, error code, authentication và concurrency contract. ERD/API phải thể hiện một case có nhiều Attempt/file evidence và nhiều Manager Decision append-only. FRD chỉ cung cấp logical data, function và hành vi mà hai tài liệu sau phải đáp ứng.
