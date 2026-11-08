# Kế hoạch kiểm thử thủ công UI cuối — `frontend/prototype`

## 1. Mục đích và phạm vi

Tài liệu này dành cho tester không cần kiến thức BA để kiểm tra thủ công giao diện tĩnh đã bàn giao
ở `frontend/prototype`. Kiểm tra gồm đăng nhập, phân quyền, hàng đợi, hồ sơ đơn, thao tác workflow,
dashboard, cài đặt, audit và khả năng dùng trên desktop/tablet/mobile.

Đây là **kế hoạch manual test**, không phải báo cáo kết quả. Mọi dòng trong cột Status bắt đầu là
`Not run`; tester ghi `Pass`, `Fail` hoặc `Blocked` và đính kèm bằng chứng. Không sửa application code
để làm test pass.

## 2. Môi trường và chuẩn bị

### URL

- Optional owner/environment-provided Windows URL: <http://172.20.92.43:4200/> (not a repository default)
- Localhost alternative when running locally: <http://localhost:4200/>
- Mở URL bằng Chrome hoặc Edge; dùng cửa sổ ẩn danh mới cho mỗi phiên nếu có thể.

### Khởi động local

Canonical setup is `make e2e`, with Docker Compose, database, API and frontend available. If the
environment owner provides an already-running URL, use it and confirm that its database/API are
healthy; otherwise the tester must have the required Docker/Compose environment:

```text
make e2e
./scripts/demo-seed.sh
```

Nếu cần khởi động đầy đủ theo quy trình local, làm theo `docs/local-development.md`, sau đó chạy
`./scripts/demo-seed.sh`. Script tạo/refresh tài khoản và 5 case synthetic (ID hex kết thúc từ
`1001` đến `1005`), không tải Olist. Script tạo credentials ngẫu nhiên một lần trong file Git-ignored
`data/evidence/P12-DEMO-CREDENTIALS.env`; không ghi password vào tài liệu, ticket hoặc ảnh chụp.

Đọc credentials an toàn trên máy chạy seed:

```text
source data/evidence/P12-DEMO-CREDENTIALS.env
printf '%s\n' "$DEMO_USERNAME"
printf '%s\n' "$DEMO_MANAGER_USERNAME"
```

Nhập từng password trực tiếp vào form, không dán vào chat. Nếu cần tạo lại, đặt
`DEMO_USERNAME`/`DEMO_PASSWORD` và `DEMO_MANAGER_USERNAME`/`DEMO_MANAGER_PASSWORD` trong môi trường
local rồi chạy lại script; phải cung cấp đủ cả username và password cho mỗi tài khoản. Không dùng
password ví dụ tự nghĩ ra.

### Reset/reseed và dữ liệu

`./scripts/demo-seed.sh` là seed **idempotent một phần**: tạo hoặc refresh user, model synthetic và
case demo còn thiếu; các thao tác manual như claim, assign, comment, complete, skip, reopen và audit
được lưu trong database. Vì vậy test workflow làm thay đổi dữ liệu và có thể ảnh hưởng test sau.

Reseeding **does not reset existing case mutations**. Before each clean group, require the environment
owner to reset the database/fixture, then run the seed and verify the baseline table. Do not treat a
seed alone as a clean reset or delete production data. Do not upload real customer data. The cases, model, scores and users
trong kế hoạch này đều synthetic.

## 3. Baseline demo cases

| Order | Risk/score | Baseline status | Baseline assignment | Mục đích |
|---|---:|---|---|---|
| `00000000000000000000000000001001` | 0.91 / HIGH | PENDING | Manager-assigned when assignment fixture is present | manager assignment/detail |
| `00000000000000000000000000001002` | 0.78 / HIGH | IN_PROGRESS | Specialist demo | comment, contact, reopen |
| `00000000000000000000000000001003` | 0.63 / MEDIUM | PENDING | Chưa assign | specialist claim, manager assign/reassign |
| `00000000000000000000000000001004` | 0.54 / MEDIUM | COMPLETED | Specialist demo | completed/read-only và audit |
| `00000000000000000000000000001005` | 0.82 / HIGH | PENDING | Chưa assign | dashboard/filter; decision only if `needs_decision` |

Seed không khôi phục mutation cũ; owner reset là bắt buộc. Xác nhận baseline trên Queue trước mỗi nhóm.

## 4. Quy ước kết quả và thứ tự chạy

1. Chạy **Smoke suite** S01–S08 sau clean reset/seed hoặc deploy.
2. Chạy Full regression theo các nhóm bên dưới; giữa mỗi nhóm phải reset DB/fixture bởi owner, seed lại,
   rồi kiểm tra baseline. Không dùng mutation của nhóm trước làm tiền điều kiện nhóm sau.
3. Kiểm tra responsive ở cuối mỗi nhóm, không coi zoom là thay đổi viewport.

Nhóm mutation: A=queue/assignment (F03–F08), B=detail/workflow (F09–F16), C=manager decisions/settings
và audit (F17–F20), D=profile/session/responsive (F21–F24). F17–F20 chỉ chạy bằng Manager.
Dashboard, Decisions, Settings và Audit đều là Manager-only; Specialist chỉ kiểm tra việc bị từ chối
khi truy cập trực tiếp các URL đó (không coi việc không thấy link là đủ).

`Pass`: UI và dữ liệu đúng expected, có bằng chứng. `Fail`: tái hiện được sai khác với expected.
`Blocked`: không thể kiểm tra vì URL/service/credential/fixture thiếu; ghi nguyên nhân, không đổi
thành Pass. `Not run`: chưa thực hiện. Không coi console warning là pass/fail nếu chưa kiểm tra ảnh
hưởng; ghi lại khi liên quan.

## 5. Smoke suite

| ID | Vai trò | Tiền điều kiện | Exact UI steps | Expected result | Status | Evidence |
|---|---|---|---|---|---|---|
| S01 | Cả hai | Chưa đăng nhập | Mở URL; nhập sai username/password; thử để trống từng ô; bấm Login | Có validation/lỗi rõ; không vào app khi thiếu hoặc sai | Not run | |
| S02 | Specialist | Có credentials seed | Đăng nhập specialist; đổi VI/EN; bật/tắt hiện password; refresh | Vào đúng app; ngôn ngữ và visibility đổi đúng; phiên còn hợp lệ | Not run | |
| S03 | Specialist | Đã login | Mở Queue; tìm ID kết thúc `1001`; mở detail rồi quay lại | Queue tải; tìm đúng case; điều hướng không mất ngữ cảnh quan trọng | Not run | |
| S04 | Specialist | ID kết thúc `1003`, MEDIUM/PENDING, clean baseline | Claim; kiểm tra status; bấm Continue | Case thành IN_PROGRESS/assigned; Continue mở workflow hợp lệ | Not run | |
| S05 | Manager | Đăng nhập manager | Mở Queue/Decision; mở ID kết thúc `1003`; assign specialist | Manager thấy chức năng manager; assignment thành công | Not run | |
| S06 | Cả hai | Có app | Truy cập trực tiếp URL của trang role khác khi chưa đủ quyền | Bị chặn hoặc chuyển trang an toàn; không lộ dữ liệu/thao tác trái quyền | Not run | |
| S07 | Manager | Có baseline | Mở Dashboard; đổi filter; mở drill-down; logout | Manager thấy số liệu/filter/drill-down; logout về Login và back không vào lại | Not run | |
| S08 | Cả hai | Có app | Thu nhỏ lần lượt desktop/tablet/mobile; mở Queue và detail | Không tràn/che nút; thao tác chính vẫn dùng được | Not run | |

## 6. Full regression suite

| ID | Vai trò | Tiền điều kiện | Exact UI steps | Expected result | Status | Evidence |
|---|---|---|---|---|---|---|
| F01 | Cả hai | Login page | Nhập username/password; toggle password; đổi ngôn ngữ; submit bằng Enter và nút; thử ô trống | Password không lộ mặc định; cả hai cách submit hoạt động; blank behavior ghi theo backend (có thể không có client validation) | Not run | |
| F02 | Cả hai | Đã login | Mở từng mục navigation; dùng URL trực tiếp cho trang hợp lệ và không hợp lệ | Link đúng role; URL sai không làm app hỏng | Not run | |
| F03 | Specialist | Queue có 5 case | Search theo order ID/product ID; dùng riêng seller/category filters; đổi risk/status; sort cột; clear; reset | Search chỉ tìm ID; seller/category là filter riêng; sort ổn định; Clear/Reset đưa về baseline | Not run | |
| F04 | Specialist | Queue | Dùng keyboard focus/tab; resize desktop 1366px, tablet 768px, mobile 390px | Focus nhìn thấy; bảng/card không cắt text; filter usable | Not run | |
| F05 | Specialist | ID kết thúc `1003`, MEDIUM/PENDING, clean baseline | Claim; thử claim lại case đã assigned; mở case của người khác | Claim hợp lệ một lần; lỗi/trạng thái rõ; không chiếm trái phép | Not run | |
| F06 | Specialist | Đã claim ID kết thúc `1003` | Bấm Continue từ case đã claim; thử tiếp tục case không được assign | Continue chỉ cho phép trạng thái hợp lệ; không có capacity/assignment page; lỗi không làm mất dữ liệu | Not run | |
| F07 | Manager | ID kết thúc `1003`, PENDING | Assign cho specialist; mở lại; reassign sang specialist khác | Assignment và audit cập nhật; người mới hiển thị đúng | Not run | |
| F08 | Manager | Có assignment | Chọn override capacity; để trống reason; nhập reason; submit | Override bắt buộc reason; submit hợp lệ lưu reason và người thực hiện | Not run | |
| F09 | Specialist | Mở ID kết thúc `1002` | Kiểm tra order detail, product/item, risk score và factors; dùng Search trong detail; Copy từng giá trị | Dữ liệu case đúng; Search navigates tới kết quả/case, không filter trong detail; Copy báo thành công và clipboard đúng | Not run | |
| F10 | Specialist | Detail ID kết thúc `1002` | Thêm comment rỗng, whitespace, comment hợp lệ; refresh | Blank behavior theo backend; comment hợp lệ hiển thị đúng author/time sau refresh | Not run | |
| F11 | Specialist | Assigned `IN_PROGRESS` case | Chọn Complete; thử submit thiếu outcome; chọn outcome và submit | Outcome là bắt buộc; complete chuyển COMPLETED và không còn thao tác sai trạng thái | Not run | |
| F12 | Specialist | Assigned `IN_PROGRESS` case | Chọn Skip; thử thiếu reason; chọn reason khác `OTHER` rồi `OTHER` kèm note; submit | Skip chỉ cho IN_PROGRESS; reason bắt buộc; `OTHER` yêu cầu note; status/lý do đúng | Not run | |
| F13 | Manager | Case đã hoàn tất/skipped và clean baseline phù hợp | Mở case; chọn Reopen; thử thiếu reason; submit hợp lệ | Reopen chỉ Manager; reason/guard đúng; cycle/status và audit đúng; không giả định confirmation | Not run | |
| F14 | Specialist | Detail assigned đang xử lý | Mở Contact attempt; để trống result; để trống các field khác; nhập result; submit | Result bắt buộc; các field khác optional; validation đúng; không có guarantee giữ draft khi lỗi | Not run | |
| F15 | Specialist | Contact form | Chọn file hợp lệ; file sai type/oversize nếu có; xóa file; submit | Tên/size hiển thị; file hợp lệ upload; file không hợp lệ bị chặn rõ | Not run | |
| F16 | Specialist | Có cycle/contact | Tạo contact attempt; chọn Complete/Skip; thử auto-skip theo điều kiện hiển thị | Attempt/outcome đúng; auto-skip theo điều kiện; không có confirmation auto-skip | Not run | |
| F17 | Manager | Manager login | Mở Dashboard; đổi available status/risk/assignee filters; clear/reset; mở card/chart | Chỉ Manager truy cập; số liệu đổi nhất quán; reset baseline; drill-down đúng Queue/detail | Not run | |
| F18 | Manager | Manager login; case `needs_decision` xuất hiện (fixture conditional) | Mở Decisions; chọn case needs_decision; thử thiếu decision rồi thiếu reason; nhập đủ và submit | Nếu không có case needs_decision, Blocked; chỉ Manager; chỉ decision/reason client-validation; không có override | Not run | |
| F19 | Manager | Manager login | Mở Settings; xem config/parameters; thử sửa giá trị, effective date, reason; cancel/save | Chỉ Manager; reason/date validation; cancel không đổi; save báo kết quả | Not run | |
| F20 | Manager | Có mutations | Mở Audit; lọc theo actor/action/case (không giả định date filter); mở chi tiết; thử copy ID | Chỉ Manager; event có actor/time/action/case; filter/clear đúng; không sửa được audit | Not run | |
| F21 | Cả hai | Đã login | Mở Profile; kiểm tra tên/username; chỉ đổi preferred language; refresh | Profile read-only ngoài language; language giữ sau refresh | Not run | |
| F22 | Cả hai | Đã login | Mở nhiều tab; logout một tab; quay lại tab kia; thực hiện protected navigation/request; dùng Back/Forward | Tab kia chỉ bị enforced ở protected request/navigation; không lộ dữ liệu; điều hướng ổn định | Not run | |
| F23 | Cả hai | Có baseline | Trên 1366x768, 1024x768, 768x1024, 390x844 kiểm tra nav, table, modal, form | Desktop/tablet/mobile không cắt control; menu/modal đóng mở được; không có scroll ngang ngoài ý muốn | Not run | |
| F24 | Cả hai | Chạy xong workflow | Refresh từng trang; mở lại các case đã mutation; logout/login lại | Dữ liệu đã lưu nhất quán; lỗi mạng nếu có được báo rõ, không báo thành công giả | Not run | |

## 7. Giới hạn cần ghi trong kết quả

- Dataset, model release, scores và orders trong kế hoạch là fixture **synthetic P12**, không phải Olist
  đầy đủ và không chứng minh chất lượng ML, causal claim hay production readiness.
- Password thật không xuất hiện trong tài liệu; chỉ lấy từ file Git-ignored do `demo-seed.sh` tạo.
- Không được tuyên bố browser E2E coverage từ việc chạy manual plan này. Manual pass chỉ chứng minh
  quan sát trên môi trường và fixture cụ thể.
- Nếu không có Docker/PostgreSQL/API hoặc không có quyền đọc credentials, các case phụ thuộc dữ liệu
  phải là `Blocked`, không phải `Pass`.
- Không coi `web/Wireframe` là sản phẩm cần test; đường dẫn bàn giao là `frontend/prototype`.

## 8. Mẫu bug report

```text
Title:
Test ID:
Environment/URL:
Viewport/browser:
Role and case/order ID:
Build/commit (if known):
Precondition and seed time:
Steps to reproduce:
Expected:
Actual:
Frequency:
Severity (Blocker/Critical/Major/Minor):
Console/network detail (redact secrets):
Evidence (screenshot/video/request ID):
Data reset needed: yes/no
```

Không đính kèm password, token, customer data hoặc file upload nhạy cảm vào bug report.

## 9. Link/path validation

Các path được dùng trong kế hoạch: [`frontend/prototype/`](../frontend/prototype/),
[`scripts/demo-seed.sh`](../scripts/demo-seed.sh), và [`docs/local-development.md`](local-development.md).
Tester nên xác nhận chúng tồn tại trong checkout trước khi bắt đầu; nếu link/path không tồn tại,
đánh dấu môi trường `Blocked` và báo owner.
