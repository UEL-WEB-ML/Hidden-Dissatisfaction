# Mục lục codebase cho AI Agent viết luận văn

Mục đích: trỏ nhanh tới đúng file khi viết `Thesis/latex`. Mỗi dòng = `đường dẫn` — tóm tắt một dòng.
Mọi đường dẫn tính từ gốc repo `Hidden-Dissatisfaction/`. Quét ngày 2026-11-04, branch `thesis`.

## 0. Quy tắc đọc trước (bắt buộc)

- **Nguồn đúng với code hiện tại:** `docs/BA_consolidated_as_built.md` (thay thế BRD 4.2 / FRD 2.2 / API cũ khi mâu thuẫn; mục 10 liệt kê chỗ lệch). Phần lớn `docs/` khác đã cũ một phần.
- **Nguồn số liệu luận văn:** `SERVER_CONTEXT/*.md` (Ch.3–4) và `reports/P5-*.md`. Chỉ lấy số từ đây, không tự suy.
- **Mọi kết quả ML là development/exploratory, không confirmatory.** Không có kết quả test niêm phong, CI bootstrap, PR/calibration curve, SHAP, budget 5/10/20% trên test (xem `SERVER_CONTEXT/chapter4_evidence.md` §8–11, `docs/incident-disclosure-p5.md`, `docs/evidence/P12-gate-0-release-boundary.md`).
- **File được trích nhưng KHÔNG có trên đĩa:** `reports/experiments/p5-s6-e15-content.json`, `reports/experiments/p5-s10-gpu-tuning.json`, `dbt/logs/dbt.log`, `artifacts/predictions/*.csv`. Chỉ trích gián tiếp qua `SERVER_CONTEXT/`.
- **`Thesis/latex/chapters/_moved_from_ch3.tex` không được `\input`.** Nó định nghĩa trùng `\label{sec:eval}` và `eq:brier` với `ch3.tex`; nếu `\input` sẽ lỗi trùng nhãn. Nội dung (Brier, Recall@k 5/10/20%, bootstrap, SHAP) là phần chưa chạy.
- **Bất biến nghiên cứu** (`CONTRIBUTING.md`, `CLAUDE.md`): đặc trưng phải biết được tại thời điểm giao; mọi item của một `order_id` cùng một phân vùng và cụm bootstrap; điểm đơn = `max-v1`; kết luận là dự báo/tương quan, không nhân quả.
- Bỏ qua: `*.aux/.log/.bbl/.bcf/.toc/.lof/.lot/.out/.fls/.fdb_latexmk/.synctex.gz/.run.xml`, `main.pdf`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `src/*.egg-info/`, `notebooks/.ipynb_checkpoints/`, `node_modules/`.

## 1. Bản đồ chương luận văn → nguồn

| Chương | File LaTeX | Trạng thái | Nguồn nên đọc |
|---|---|---|---|
| Lời cảm ơn, cam kết, viết tắt, tóm tắt | `Thesis/latex/main.tex` (inline) | Trống / TODO | `web/BaoCao_LaTeX/loi-cam-on.tex`, `web/BaoCao_LaTeX/chuong/00-tom-tat.tex` (mẫu của báo cáo môn Web) |
| 1. Giới thiệu | `Thesis/latex/main.tex` (inline, chỉ heading) | Trống | `docs/problem_statement_olist_hidden_dissatisfaction.md`, `docs/report-olist-hidden-dissatisfaction-literature-review-2026-09-26.md`, `docs/research-design.md`, `web/BaoCao_LaTeX/chuong/01-gioi-thieu.tex` (bản nháp 149 dòng), `notebooks/01_eda_why_lateness_dominates.ipynb` |
| 2. Cơ sở lý thuyết | `chapters/ch2.tex` | Stub (3 section TODO) | `docs/report-olist-hidden-dissatisfaction-literature-review-2026-09-26.md` (gap 1–6), `docs/end_to_end_machine_learning_theory_olist_hidden_dissatisfaction.md`, `references/*.md`, `Thesis/latex/references.bib` |
| 3. Phương pháp | `chapters/ch3.tex` | Đã viết (271 dòng) | `SERVER_CONTEXT/chapter3_evidence.md`, `rolling_origin_folds.md`, `label_snapshot_build_evidence.md`, `docs/research-design.md`, `docs/data-contract.md`, `docs/modeling-training-plan.md`, ADR-001/008/010/014, `configs/experiment.toml` |
| 4. Kết quả | `chapters/ch4.tex` | Stub (3 section TODO) | `SERVER_CONTEXT/chapter4_evidence.md`, `SERVER_CONTEXT/model_variant_fold_metrics.md`, `reports/P5-accuracy-coursework-summary.md`, `reports/P5-S1…S10-*.md`, `docs/evidence/P5-development-gate-2026-10-23.md` |
| 5. Thảo luận | `Thesis/latex/main.tex` (inline, chỉ heading) | Trống | `reports/P5-accuracy-failure-analysis.md`, `reports/P5-accuracy-coursework-summary.md` §Interpretation, `docs/evidence/P12-gate-0-release-boundary.md`, `docs/problem_statement_olist_hidden_dissatisfaction.md` §7 (tiêu chí thành công) |
| 6. Kết luận, đề xuất | `Thesis/latex/main.tex` (inline, chỉ heading) | Trống | `reports/P5-accuracy-failure-analysis.md`, `planning.md` §8 P12 & §13, `docs/BA_consolidated_as_built.md` §10, `HISTORY.md` §Blocker |
| Phụ lục A | `chapters/appendix_a.tex` | Đã viết | `SERVER_CONTEXT/chapter3_evidence.md` §5–6 |
| Phụ lục B "Tài liệu bổ trợ" | `Thesis/latex/main.tex` (inline) | Trống | `docs/BA_consolidated_as_built.md`, `docs/API_CONTRACT_olist_hidden_dissatisfaction.md`, `web/SoDo/`, `docs/system-architecture.drawio.png` |

Nếu viết phần hệ thống/ứng dụng: `docs/BA_consolidated_as_built.md`, `docs/feature-flow-guide.vi.md`, `docs/architecture.md`, `docs/architecture-code-map.md`.

## 2. Số liệu tra nhanh (đã kiểm chứng trong nguồn)

- Olist: 99,441 đơn / 112,650 item / 9 CSV — `ch3.tex` tab:olist, `SERVER_CONTEXT/chapter3_evidence.md` §2.
- Phễu quần thể: 99,441 → 96,478 (delivered) → 88,644 (đúng/sớm hạn) → 85,420 đơn / 97,878 item (có review sau giao) — `chapter3_evidence.md` §2.
- Snapshot huấn luyện: **85,425 đơn / 97,884 item** (lệch 5 đơn / 6 item so với dựng lại) — `chapter3_evidence.md` §2, `label_snapshot_build_evidence.md`.
- 6 phân vùng thời gian (mốc 2017-10-01 / 2017-12-01 / 2018-02-01 / 2018-04-01 / 2018-06-01 / 2018-09-01), tỉ lệ dương 10.13–13.80%, test ẩn — `chapter3_evidence.md` §1, `configs/experiment.toml`.
- 3 fold rolling-origin, ngày bắt đầu kiểm định 2017-06-01 / 2017-07-18 / 2017-08-24 — `SERVER_CONTEXT/rolling_origin_folds.md`.
- Mô hình giữ lại: `order_weight:random_forest-depth8-leaf5-v1`, 200 cây, `balanced_subsample`, seed 42, hiệu chỉnh sigmoid (Brier so sánh 0.104947 vs isotonic 0.105665 vs none 0.220332) — `chapter3_evidence.md` §3–4.
- Kết quả rolling (trung bình): item PR-AUC 0.176017, order PR-AUC 0.146502, order Brier 0.190663, Recall@5% 0.121225; selection-holdout order PR-AUC 0.210761 — `chapter4_evidence.md` §7, `reports/P5-accuracy-failure-analysis.md`.
- CatBoost GPU challenger theo fold — `SERVER_CONTEXT/model_variant_fold_metrics.md`.
- Ngưỡng: top 5% đơn = HIGH, top 20% = MEDIUM trở lên; `high_from=0.2857879098`, `medium_from=0.1119326946` (run RF cũ hơn) — `chapter4_evidence.md`.
- 61 đặc trưng, 7 nhóm, schema `p5-item-v11-interactions` — `chapter3_evidence.md` §5, `appendix_a.tex`, `src/hidden_dissatisfaction/modeling/schema.py`.
- Môi trường: Python ≥3.11, pandas 2.3.3, NumPy 2.4.6, scikit-learn 1.9.1, CatBoost 1.2.10, dbt 1.8.10, commit `6e8976f` — `chapter3_evidence.md` §6.

## 3. Thesis/

- `Thesis/latex/main.tex` — Khung luận văn (bìa, mục lục, Ch.1/5/6 inline chỉ heading, `\input` ch2/ch3/ch4/appendix_a, biblatex).
- `Thesis/latex/chapters/ch2.tex` — Stub Ch.2 Cơ sở lý thuyết: `ch:theory`, `sec:concepts`, `sec:related`, `sec:theory-models`.
- `Thesis/latex/chapters/ch3.tex` — Ch.3 Phương pháp đầy đủ: bài toán + `eq:maxv1`, pipeline 7 bước (`fig:ml-flow`, `fig:arch`), dữ liệu (`tab:olist`, `tab:funnel`), rò rỉ (`fig:leakage-timeline`, `tab:features`), mô hình, chia thời gian (`tab:split`, `fig:temporal-folds`), hiệu chỉnh/ngưỡng, đánh giá (`sec:eval`, `eq:brier`). Ghi chú: còn viết cứng "Chương~4" ở dòng 177 và 271 thay vì `\ref{ch:results}`.
- `Thesis/latex/chapters/ch4.tex` — Stub Ch.4 Kết quả: `ch:results`, `sec:results`, `sec:tables`, `sec:analysis`.
- `Thesis/latex/chapters/appendix_a.tex` — Phụ lục A: từ điển khái niệm (`tab:app-dict`), danh mục 61 đặc trưng (`tab:feature-list`), cấu hình chạy (`tab:app-env`).
- `Thesis/latex/chapters/_moved_from_ch3.tex` — Phần đánh giá bị cắt khỏi Ch.3 (chưa chạy); KHÔNG `\input` (xem mục 0).
- `Thesis/latex/references.bib` — 12 mục: olist2018, orman2026, ravula2023, brylla2022, vandengoorbergh2022, li2008, gomezvargas2025, zaghloul2024, deshpande2023, ascarza2018, elor2022smote, li2026valuesorting.
- `Thesis/latex/images/system-architecture.png` — Hình kiến trúc dùng ở `fig:arch` (bản gốc: `docs/system-architecture.drawio`).
- `Thesis/latex/images/cover-kl01-vi.jpg`, `cover-kl01-en.jpg` — Ảnh bìa theo mẫu UEL.
- `Thesis/latex/ML _ MASTERSHEET.xlsx` — Sheet quản lý nhóm: CHECKLIST, TIMELINE, BUSINESS PROBLEMS, LƯỢC KHẢO, RESOURCE.
- `Thesis/Outline final project.docx.md` — Dàn ý bắt buộc của khóa luận (Title → Abstract → 1..6 → TLTK → phụ lục).
- `Thesis/Huong dan khoa luan tot nghiep 2025 - Khoa HTTT.doc` — Quy định trình bày khóa luận Khoa HTTT (file .doc nhị phân).
- `Thesis/PHU LUC 7 CACH TRICH TAI LIEU THAM KHAO.pdf` — Quy định trích dẫn tài liệu tham khảo.

## 4. SERVER_CONTEXT/ (bằng chứng số liệu cho Ch.3–4)

- `SERVER_CONTEXT/README.md` — Mục lục các file bằng chứng; chỉ số liệu tổng hợp, không dữ liệu dòng.
- `SERVER_CONTEXT/chapter3_evidence.md` — Phân vùng thời gian, phễu quần thể, cô lập hiệu chỉnh, cấu hình mô hình, 61 đặc trưng, môi trường.
- `SERVER_CONTEXT/chapter4_evidence.md` — Kết quả 3 fold của RF giữ lại + bảng những gì KHÔNG có (test, budget, predictions, SHAP).
- `SERVER_CONTEXT/model_variant_fold_metrics.md` — Metric theo fold: RF giữ lại và 3 biến thể CatBoost GPU; báo rõ không có so sánh đầy đủ các họ khác.
- `SERVER_CONTEXT/rolling_origin_folds.md` — Ngày và số dòng train/validation của 3 fold (cho Hình 3.3).
- `SERVER_CONTEXT/label_snapshot_build_evidence.md` — Log dbt chứng minh snapshot 97,884 dòng (source run `6f13bf55…`).

## 5. reports/ (quyết định thực nghiệm P5)

- `reports/README.md` — Quy ước: chỉ commit bảng/hình tái lập được; `render_report` ghi vào `reports/figures` (hiện chưa có).
- `reports/P12-report-evidence-index.md` — Bảng "vùng claim → file nguồn → độ tin cậy" cho báo cáo; đọc trước khi viết claim.
- `reports/P5-accuracy-coursework-summary.md` — Tóm tắt 10 pha S1–S10, tập đặc trưng cuối, kết quả CatBoost, giới hạn diễn giải.
- `reports/P5-accuracy-failure-analysis.md` — Vì sao kế hoạch dừng dưới mục tiêu; số cuối của RF giữ lại; hướng tiếp theo.
- `reports/P5-S1-target-history-ablation.md` — S1: lịch sử nhãn seller/danh mục với Bayesian smoothing.
- `reports/P5-S2-seller-operations-ablation.md` — S2: tốc độ/độ biến động seller (được giữ).
- `reports/P5-S3-geography-ablation.md` — S3: logistics & địa lý (Haversine).
- `reports/P5-S4-order-composition-ablation.md` — S4: số lượng, tỉ lệ, HHI trong đơn (được giữ).
- `reports/P5-S5-payment-behavior-ablation.md` — S5: hành vi thanh toán.
- `reports/P5-S6-product-morphology-ablation.md` — S6: hình thái sản phẩm & độ đầy đủ nội dung (được giữ).
- `reports/P5-S7-temporal-features-ablation.md` — S7: lịch và khối lượng theo thời gian.
- `reports/P5-S8-data-quality-ablation.md` — S8: cờ chất lượng dữ liệu.
- `reports/P5-S9-interactions-ablation.md` — S9: tương tác có kiểm soát.
- `reports/P5-S10-feature-selection.md` — S10: leave-one-group-out và chốt tập đặc trưng.

## 6. docs/

### 6.1 Nghiên cứu và hợp đồng dữ liệu
- `docs/README.md` — Mục lục tài liệu theo thứ tự đọc.
- `docs/problem_statement_olist_hidden_dissatisfaction.md` — Bối cảnh, khoảng trống, câu hỏi/mục tiêu nghiên cứu, tiêu chí thành công, phạm vi (nguồn chính Ch.1).
- `docs/report-olist-hidden-dissatisfaction-literature-review-2026-09-26.md` — Lược khảo: 6 gap, RQ, giả thuyết, ranh giới diễn giải (nguồn chính Ch.2).
- `docs/research-design.md` — Câu hỏi chính, estimand, đơn vị item/đơn, metric bắt buộc.
- `docs/data-contract.md` — 9 file CSV, quy tắc kiểm tra, định nghĩa cohort/nhãn.
- `docs/end_to_end_machine_learning_theory_olist_hidden_dissatisfaction.md` — Lý thuyết ML end-to-end (837 dòng): point-in-time, split, calibration, threshold, đánh giá.
- `docs/modeling-training-plan.md` — Phạm vi cài đặt huấn luyện P5 (v1→v5) theo ADR-010..014.
- `docs/model-accuracy-improvement-plan.md` — Kế hoạch S0–S10, công thức đặc trưng, guardrail, gate giữ nhóm.
- `docs/incident-disclosure-p5.md` — Công bố sự cố timeout P5; kết quả phải giữ nhãn `exploratory_non_confirmatory`.

### 6.2 Nghiệp vụ, API, dữ liệu web
- `docs/BA_consolidated_as_built.md` — **BA as-built**: người dùng, màn hình, vòng đời case, SLA, liên lạc, tham số, queue/dashboard, schema ml/app/bronze, tích hợp mô hình, chỗ lệch tài liệu cũ.
- `docs/BRD_olist_hidden_dissatisfaction.md` — BRD v4.2: persona, phạm vi, business rules 6.1–6.12, tiêu chí nghiệm thu.
- `docs/FRD_olist_hidden_dissatisfaction.md` — FRD v2.2: chức năng F01–F12, actor, trạng thái.
- `docs/API_CONTRACT_olist_hidden_dissatisfaction.md` — API 0.5: quy ước, đối tượng, endpoint, truy vết FRD→endpoint.
- `docs/DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md` — Từ điển dữ liệu v0.5 các bảng `app.*` và view `ml.v_risk_*_for_web`.
- `docs/ERD_olist_hidden_dissatisfaction.md` — ERD logic P7 (6 bảng schema `app`).
- `docs/traceability.md` — Ma trận BRD → FRD → API → DB → backend → frontend → test.
- `docs/feature-flow-guide.vi.md` — Luồng hệ thống từng feature F00–F12 kèm thành phần để vẽ sequence diagram.

### 6.3 Kiến trúc và vận hành
- `docs/architecture.md` — Các lớp clean architecture và điều mỗi lớp không được làm.
- `docs/architecture-code-map.md` — Entry point và đường đi runtime/warehouse/ML có trích dòng code.
- `docs/system-architecture.drawio` / `.drawio.png` / `.excalidraw` — Sơ đồ kiến trúc (sinh bởi `scripts/generate_architecture_*`); `docs/assets/architecture-icons/*.svg` là icon.
- `docs/local-development.md` — Cài đặt Python/uv, Postgres, dbt, frontend cục bộ.
- `docs/environment-manifest.md` — Toolchain cần ghi lại khi release check.
- `docs/consolidation-manifest.md` — Gộp repo ML_docs + Docker_Environment vào repo này (2026-10-21).
- `docs/P12-gate-2-demo.md` — Runbook demo synthetic.

### 6.4 ADR (quyết định thiết kế)
- `docs/adr/ADR-001-multiple-review-policy.md` — Đơn nhiều review: chọn review được trả lời mới nhất.
- `docs/adr/ADR-002-timezone-api-datetime.md` — Lưu `timestamptz` UTC, API trả ISO-8601.
- `docs/adr/ADR-003-api-authentication.md` — JWT Bearer, Argon2 qua pwdlib, logout stateless.
- `docs/adr/ADR-004-sla-calendar.md` — SLA theo lịch thường; BUSINESS_HOURS hoãn.
- `docs/adr/ADR-005-decision-outcome-skip-catalogues.md` — Danh mục outcome/decision/skip reason.
- `docs/adr/ADR-006-evidence-storage-retention.md` — Port lưu minh chứng, giữ 24h cho upload chưa gắn.
- `docs/adr/ADR-007-mutable-parameters.md` — Manager sửa được mọi tham số vận hành.
- `docs/adr/ADR-008-review-observation-window.md` — Dự đoán tại `delivered_customer_date`; review phải tạo sau thời điểm này.
- `docs/adr/ADR-009-synthetic-item-policy.md` — Dữ liệu synthetic chỉ cho demo, không là bằng chứng.
- `docs/adr/ADR-010-p5-training-protocol.md` — Giao thức huấn luyện/đánh giá P5 v1.
- `docs/adr/ADR-011-p5-gpu-candidate.md` — P5 v2: thêm ứng viên CatBoost GPU.
- `docs/adr/ADR-012-p5-native-categorical-tuning.md` — P5 v3: CatBoost categorical native.
- `docs/adr/ADR-013-p5-delivery-product-features.md` — P5 v4: đặc trưng giao hàng và sản phẩm.
- `docs/adr/ADR-014-p5-order-level-challenger.md` — P5 v5: chế độ `order_aggregate`.

### 6.5 Bằng chứng gate và release
- `docs/evidence/P5-development-gate-2026-10-23.md` — Gate P5: bronze run, dbt 68 pass, metric development.
- `docs/evidence/P10-frontend-dependency-audit-2026-10-29.md` — npm audit 54 lỗi → hết sau nâng Angular 22.
- `docs/evidence/P11-runtime-gate-2026-10-29.md` — Compose E2E và walkthrough synthetic đã pass.
- `docs/evidence/P12-gate-0-release-boundary.md` — Ma trận được/không được claim; release confirmatory bị chặn.
- `docs/release/P12-gate-3-release-candidate.md` — Checklist RC `0.1.0-demo.3`.

## 7. Gốc repo và cấu hình

- `README.md` — Hợp đồng dự án (grain item/order), layout repo, setup, quality gate, trạng thái hiện tại, ranh giới release.
- `CLAUDE.md` — Hướng dẫn agent: lệnh, kiến trúc, bất biến nghiên cứu.
- `CONTRIBUTING.md` — Quy tắc đóng góp và bất biến chống rò rỉ.
- `HISTORY.md` — Lịch sử dự án theo mốc thời gian, thành viên, checkpoint S1–S10, blocker (nguồn cho phần quá trình thực hiện).
- `planning.md` — Kế hoạch P0–P12 (1315 dòng), DoR/DoD, test matrix, quality gate, rủi ro, checklist hoàn thành.
- `RELEASE_NOTES.md` — Ghi chú bản demo `0.1.0-demo.3`.
- `configs/experiment.toml` — Cấu hình thực nghiệm: cohort, mốc chia, metric, budget, họ mô hình, biến thể, regime, calibration.
- `pyproject.toml`, `uv.lock`, `.python-version` — Phụ thuộc Python (extra dev/ml/api/db), Python 3.11.
- `Makefile` — Target: install, quality, bootstrap, bronze-manifest, ingest, warehouse, train, score, demo-seed, app-up, e2e, release-check, migrate, p4-release-verify.
- `compose.yaml` — Dịch vụ: postgres, migrate, api, frontend, frontend-test, warehouse.
- `.github/workflows/quality.yml` — CI: ruff, black, mypy, pytest (100% coverage domain+application), frontend lint/test/build, Postgres integration.
- `.env.example`, `.dockerignore`, `.gitignore`, `.pre-commit-config.yaml` — Biến môi trường mẫu và cấu hình công cụ.
- `main.py` — Hello-world thừa từ template, không dùng.

## 8. src/hidden_dissatisfaction/ (Python package)

### 8.1 domain/ (luật thuần, không I/O)
- `domain/cohort.py` — Luật quần thể và nhãn (review 1–2 sao, lý do loại trừ, `OrderObservation`).
- `domain/scoring.py` — `aggregate_max_v1`: điểm đơn = max điểm item.
- `domain/workflow.py` — Chính sách case: claim, close, contact, reopen, assign, comment, decision, nhận dạng loại file minh chứng.
- `domain/case_metrics.py` — SLA, aging, stale, dải điểm và cấu trúc Dashboard.
- `domain/queue.py` — Bộ lọc và kiểm tra tham số truy vấn Risk Queue.
- `domain/parameters.py` — Định nghĩa và kiểm tra thay đổi tham số vận hành (kể cả luật chéo).
- `domain/configuration.py` — Value object: bundle tham số, capacity, ngưỡng ML.
- `domain/auth.py` — Role (SPECIALIST/MANAGER), User, token, lỗi xác thực.
- `domain/exceptions.py` — Lỗi miền gốc.

### 8.2 application/ (use case + port)
- `application/ports.py` — Port: nguồn quan sát đơn, metadata release, ngưỡng, snapshot, ghi dự đoán, nạp model.
- `application/release_scoring.py` — Use case chấm điểm theo lô: nạp model, tính điểm item, max-v1, gán mức, ghi nguyên tử.
- `application/bronze_ingestion.py` — Đặc tả 9 file bronze, manifest SHA-256, kiểm tra, đọc CSV.
- `application/modelling_export.py` — Hợp đồng xuất bảng modelling item (chuẩn hóa, kiểm tra).
- `application/summarize_cohort.py` — Đếm kiểm toán khi dựng quần thể chính.
- `application/queue.py` — DTO và port Risk Queue, tóm tắt hàng đợi.
- `application/queue_seeding.py` — Seed case từ một prediction run đang active.
- `application/workflow_commands.py` — Port ghi workflow (assign, contact, decision, evidence).
- `application/claim.py` — Port claim case.
- `application/parameters.py` — Lệnh tạo phiên bản tham số append-only.
- `application/configuration.py` — Use case đọc tham số hiệu lực, capacity, ngưỡng ML.
- `application/auth.py` — AuthService: đăng nhập, phát/kiểm JWT, băm mật khẩu.

### 8.3 modeling/ (pipeline ML)
- `modeling/schema.py` — Hợp đồng bảng modelling item: danh sách đặc trưng theo nhóm, target, kiểm tra schema (nguồn tên 61 đặc trưng).
- `modeling/splitting.py` — Chia thời gian nhóm theo đơn, 6 phân vùng, rolling-origin folds.
- `modeling/estimators.py` — Các ứng viên: prevalence, logistic, RF, HistGB, CatBoost; tiền xử lý fit trong fold; sample weight.
- `modeling/training.py` — Điều phối: chọn mô hình, regime, hiệu chỉnh, ngưỡng capacity, artifact, checkpoint, metadata tái lập.
- `modeling/evaluation.py` — Metric phân loại/hiệu chỉnh, gộp đơn, bootstrap theo cụm đơn, metric theo budget.
- `modeling/reporting.py` — Vẽ PR curve, calibration curve, bảng budget từ artifact đã niêm phong (chưa có artifact để chạy).

### 8.4 infrastructure/ (adapter)
- `infrastructure/postgres_release_scoring.py` — Đọc release, ghi snapshot dự đoán bất biến vào `ml`.
- `infrastructure/joblib_model_artifact.py` — Nạp và kiểm tra envelope model joblib (SHA, schema version).
- `infrastructure/modelling_parquet_exporter.py` — Xuất parquet modelling items nguyên tử kèm manifest và git SHA.
- `infrastructure/postgres_modelling_items_reader.py` — Đọc `gold.ml_modelling_items` theo allowlist cột.
- `infrastructure/postgres_bronze_ingestion.py` — Nạp bronze bất biến theo run.
- `infrastructure/postgres_risk_queue.py` — Truy vấn Risk Queue cấp đơn.
- `infrastructure/postgres_case_reads.py` — Read model Order Detail, Dashboard, Audit.
- `infrastructure/postgres_workflow_commands.py` — Giao dịch ghi workflow case (549 dòng).
- `infrastructure/postgres_claim_case.py` — Claim có kiểm tra capacity/xung đột.
- `infrastructure/postgres_queue_seeding.py` — Seed case vào `app`.
- `infrastructure/postgres_parameters.py` — Ghi phiên bản tham số append-only.
- `infrastructure/postgres_configuration.py` — Đọc cấu hình hiệu lực.
- `infrastructure/postgres_operational_reads.py` — Read model cấu hình và danh sách specialist.
- `infrastructure/postgres_users.py` — Repository người dùng.
- `infrastructure/sla_recalculation.py` — Tính lại SLA case đang mở khi tham số SLA đổi.
- `infrastructure/local_evidence_store.py` — Lưu minh chứng trên volume cục bộ.
- `infrastructure/evidence_cleanup.py` — Xóa upload chưa gắn sau thời hạn (ADR-006).
- `infrastructure/database.py` — Session factory SQLAlchemy async.

### 8.5 api/ và interfaces/
- `api/app.py` — FastAPI app: auth, config, parameters, queue, claim, xử lý lỗi, CORS.
- `api/workflow_routes.py` — Route Order Detail, thao tác workflow, evidence, Dashboard, Audit.
- `api/schemas.py` — Pydantic request/response.
- `api/dependencies.py` — Nối adapter Postgres vào service.
- `api/authorization.py` — `require_manager`.
- `api/config.py` — Settings (tiền tố `HD_`).
- `interfaces/cli.py` — CLI `hidden-dissatisfaction`: tóm tắt cohort, export, train, score, seed.

## 9. dbt/ (kho dữ liệu medallion)

- `dbt/dbt_project.yml`, `dbt/profiles.yml`, `dbt/models/sources.yml` — Cấu hình dbt và khai báo nguồn bronze.
- `dbt/macros/` — `generate_schema_name`, `source_run` (lọc theo run ID), `test_unique_combination_of_columns`.

Silver (chuẩn hóa từ bronze):
- `dbt/models/silver/stg_orders.sql`, `stg_order_items.sql`, `stg_order_payments.sql`, `stg_order_reviews.sql`, `stg_customers.sql`, `stg_sellers.sql`, `stg_products.sql` (kèm dịch danh mục), `stg_geolocation.sql` — Mỗi file chuẩn hóa một bảng Olist.
- `dbt/models/silver/geolocation_zip.sql` — Gộp tọa độ về một dòng mỗi mã bưu chính.
- `dbt/models/silver/schema.yml` — Test cột silver.

Intermediate P4 (quần thể và lịch sử):
- `int_p4_review_canonical.sql` — Chọn một review mỗi đơn theo ADR-001.
- `int_p4_item_base.sql` — Dòng item gốc từ order_items.
- `int_p4_payment_features.sql` — Gộp thanh toán về một dòng mỗi đơn.
- `int_p4_cohort.sql` — Quần thể chính: đơn giao đúng/sớm hạn, có review sau giao, kèm nhãn.
- `int_p4_history.sql` — Lịch sử review seller/danh mục trước mốc dự đoán (cận trên mở); `int_p4_history_unit.yml` là unit test.

Intermediate P5 (nhóm đặc trưng S1–S9):
- `int_p5_target_history.sql` — S1 lịch sử nhãn có làm trơn (+ `int_p5_target_history_unit.yml`).
- `int_p5_seller_operations.sql` — S2 tốc độ/độ biến động seller.
- `int_p5_geography.sql` — S3 khoảng cách và địa lý.
- `int_p5_order_composition.sql` — S4 số lượng, tỉ lệ, HHI trong đơn.
- `int_p5_payment_behavior.sql` — S5 hành vi thanh toán.
- `int_p5_product_morphology.sql` — S6 hình thái sản phẩm và độ đầy đủ nội dung.
- `int_p5_temporal_features.sql` — S7 lịch và khối lượng theo ngày (loại ngày cutoff).
- `int_p5_data_quality.sql` — S8 cờ chất lượng dữ liệu.
- `int_p5_interactions.sql` — S9 tương tác theo giả thuyết.

Gold:
- `dbt/models/gold/ml_modelling_items.sql` — **Bảng mô hình hóa mức item** nối cohort + mọi nhóm đặc trưng.
- `order_reviews_canonical.sql`, `fct_orders.sql`, `fct_order_items.sql`, `fct_payments.sql`, `fct_reviews.sql` — Bảng sự kiện.
- `dim_customer.sql`, `dim_seller.sql`, `dim_product.sql`, `dim_date.sql`, `dim_zip_centroid.sql` — Bảng chiều.
- `bridge_order_category.sql`, `bridge_order_seller.sql` — Bảng cầu đơn–danh mục, đơn–seller.
- `mart_order_dashboard.sql`, `mart_order_item_dashboard.sql` — Mart cho dashboard phân tích.
- `gold_schema.yml` — Test cột gold.

dbt/tests/ (37 test SQL):
- `p4_*.sql` (12) — Bất biến P4: cohort/cutoff, khóa xác định, lịch sử sớm nhất = 0, không lẫn run, khử trùng sự kiện, support, hợp đồng review, trọng số tổng = 1.
- `p5_<nhóm>_row_grain.sql` — Mỗi nhóm P5 đúng một dòng mỗi item.
- `p5_<nhóm>_invariants.sql` — Miền giá trị hợp lệ của nhóm.
- `p5_<nhóm>_*reconciliation.sql`, `*_order_consistency.sql` — Đối chiếu với nguồn và nhất quán trong đơn.

## 10. infra/ (PostgreSQL, Docker)

- `infra/postgres/init/00-roles-and-schemas.sql` — Tạo role (owner, migrator, app_runtime, ingest_writer, transform_runner, reader) và schema app/bronze/gold/ml.
- `infra/postgres/init/01-default-privileges.sql` — Quyền mặc định theo role.
- `infra/postgres/init/02-create-app-api-login.sh` — Tạo login cho API.
- `infra/postgres/migrate.sh` — Runner migration psql forward-only.
- `infra/postgres/migrations/README.md` — Quy ước migration.
- `V001__p6_1_prediction_contract.sql` — Schema `ml`: model_releases, predictions, điểm item/đơn, thresholds, trigger bất biến.
- `V002__p6_2_contract_corrections.sql` — Sửa hợp đồng; view `ml.v_risk_orders_for_web`, `ml.v_risk_items_for_web`.
- `V003__p7_app_case_cycle_baseline.sql` — `app.users`, `review_cases`, `review_cycles`.
- `V004__p7_parameters_audit_baseline.sql` — `parameter_definitions`, `parameters`, `audit_events` bất biến + seed.
- `V005__p7_integrity_and_runtime_grants.sql` — Quyền runtime.
- `V006__p7_workflow_entities.sql` — Bảng assignments, contact_attempts, contact_evidence, case_comments, manager_decisions.
- `V007__p7_audit_corrections_and_parameter_bundles.sql` — `audit_corrections`, `parameter_bundles`.
- `V008__p9_queue_blockers.sql` — Hàm đóng cycle và guard.
- `V009__p8_runtime_user_language_grant.sql` — Quyền đổi ngôn ngữ người dùng.
- `V010__p9_parameter_runtime_grants.sql` — Quyền ghi tham số.
- `V011__p9_seed_initial_parameter_bundle.sql` — Seed bundle tham số đầu.
- `V012__p9_workflow_contract_fields.sql` — Thêm trường theo API 0.5.
- `V013__p9_attempt_cycle_and_evidence_uploads.sql` — Số attempt theo cycle, bảng upload minh chứng.
- `V014__p9_case_guard_security_definer.sql` — Guard đọc điểm ML với quyền owner.
- `V015__p9_read_path_indexes.sql` — Index cho Queue/Dashboard (đo bằng `scripts/bench_queue.py`).
- `V016__p9_active_thresholds_view.sql` — View ngưỡng ML đang active.
- `V017__p9_sla_adjustments.sql` — Bảng điều chỉnh SLA khi tham số đổi.
- `V018__p9_evidence_upload_retention.sql` — Cho phép xóa upload chưa gắn.
- `V019__p2_bronze_ingestion_contract.sql` — Bảng bronze dạng text + lineage run.
- `V020__synthetic_demo_prediction_contract.sql` — Trạng thái SYNTHETIC_DEMO cho snapshot demo.
- `infra/api/Dockerfile`, `infra/jobs/Dockerfile` — Image API và job (dbt/train/score).

## 11. tests/

- `tests/unit/test_cohort.py`, `test_summarize_cohort.py` — Quần thể và nhãn.
- `tests/unit/test_modeling_schema.py`, `test_modeling_splitting.py`, `test_modeling_training.py`, `test_modeling_evaluation.py`, `test_modeling_reporting.py` — Pipeline ML.
- `tests/unit/test_modelling_export.py`, `test_gold_reader_export.py`, `test_bronze_ingestion.py` — Export và nạp dữ liệu.
- `tests/unit/test_release_scoring.py`, `test_p4_p6_contracts.py` — Chấm điểm và hợp đồng P4–P6.
- `tests/unit/test_workflow.py`, `test_workflow_routes.py`, `test_p9_policies.py`, `test_case_metrics.py`, `test_queue.py` — Workflow, route, SLA, queue.
- `tests/unit/test_parameters.py`, `test_create_parameter_version.py` — Tham số.
- `tests/unit/test_api_foundation.py`, `test_api_authorization.py` — Nền API và phân quyền.
- `tests/contract/test_api_contract.py` — OpenAPI khớp API Contract 0.5.
- `tests/integration/test_postgres_*.py` — Tích hợp Postgres (bronze, parameters, release scoring, workflow 14 test); cần DSN.
- `tests/integration/test_training_pipeline.py` — Huấn luyện end-to-end trên dữ liệu nhỏ.
- `tests/sql/p6_1_contract.sql` … `p9_queue_blockers_contract.sql` — Kiểm cấu trúc DB sau migration.
- `tests/smoke.sh`, `tests/demo_e2e.sh` — Smoke test và walkthrough demo có xác thực.
- `tests/acceptance/README.md`, `tests/integration/README.md` — Quy ước test.

## 12. frontend/hidden-dissatisfaction-frontend/ (Angular, "Signal Desk")

- `README.md`, `package.json`, `angular.json`, `Dockerfile`, `nginx.conf` — Cấu hình và đóng gói frontend.
- `src/app/app.routes.ts` — Route: login, queue, decisions, orders/:id (+ /attempt, /decision), dashboard, audit, parameters, profile.
- `src/app/core/api-client.service.ts`, `api-dtos.ts` — Client `/api/v1` có kiểu.
- `src/app/core/auth.store.ts`, `guards.ts`, `interceptors.ts` — Trạng thái đăng nhập (Signals), guard vai trò, interceptor ngôn ngữ/auth/lỗi.
- `src/app/layout/app-shell.component.ts` — Khung giao diện.
- `src/app/features/queue/*` — Màn Risk Queue (component, store, mapper, model).
- `src/app/features/order-detail/*` — Chi tiết đơn và thao tác (store, facade, mapper).
- `src/app/features/attempt/*` — Ghi lần liên lạc và minh chứng.
- `src/app/features/decision/*` — Quyết định của Manager.
- `src/app/features/dashboard/*` — Dashboard rủi ro.
- `src/app/features/audit/*` — Lịch sử audit.
- `src/app/features/parameters/*` — Cấu hình tham số (Manager).
- `src/app/features/auth/login.component.ts`, `src/app/features/profile/profile.component.ts` — Đăng nhập, hồ sơ.
- `src/app/shared/states.component.ts`, `features/placeholder/*` — Trạng thái loading/empty/error, trang giữ chỗ.
- `*.spec.ts` — Unit test Karma tương ứng.

## 13. notebooks/ và dữ liệu

- `notebooks/01_eda_why_lateness_dominates.ipynb` — EDA: 5 lý do mô hình Olist chỉ dự báo giao trễ; phân khúc "đúng hạn nhưng không hài lòng" (động lực đề tài, Ch.1–2).
- `notebooks/olist_open_eda.ipynb` — EDA mở: cấu trúc, join, chất lượng dữ liệu, thời gian, seller, sản phẩm, địa lý, review.
- `notebooks/02_modelling_dataset.ipynb` — Nạp và đối chiếu bảng modelling items.
- `notebooks/03_modeling_and_training.ipynb` — Chạy huấn luyện, so sánh mô hình, budget (khung).
- `notebooks/03_model_evaluation.ipynb` — Gọi `render_report` (cần artifact chưa có).
- `notebooks/figures/01_coverage.png` … `16_correlations.png` — 16 hình EDA dùng được cho Ch.1/3 (coverage, nhịp tuần, vận hành, tập trung, khách lặp, danh mục, giá–phí, thanh toán, hứa–thực, bang, địa lý, luồng vùng, review, yếu tố điểm, chủ đề văn bản, tương quan).
- `notebooks/README.md`, `notebooks/dataset/about_dataset.md`, `image.png` — Quy ước notebook; mô tả bộ dữ liệu Olist từ Kaggle và sơ đồ schema.
- `data/raw/olist/*.csv` — 9 CSV Olist gốc (không commit).
- `data/processed/order_features.parquet`, `modelling_orders.parquet` (+ `.manifest.json`) — Bảng cấp đơn kiểu cũ, không phải snapshot item hiện tại.
- `data/*/README.md`, `artifacts/README.md` — Quy ước thư mục dữ liệu và artifact (artifact hiện trống).

## 14. scripts/

- `scripts/run-s1-ablations.sh` … `run-s9-ablations.sh` — Chạy ablation từng pha S1–S9 với RF cố định.
- `scripts/run-s10-leave-one-group-out.sh`, `run-s10-gpu-tuning.sh` — S10: bỏ từng nhóm; tinh chỉnh CatBoost GPU.
- `scripts/release-check.sh`, `clean-checkout-check.sh` — Kiểm tra trước release.
- `scripts/demo-seed.sh` — Tạo tài khoản và dữ liệu demo synthetic.
- `scripts/bench_queue.py` — Đo tốc độ Queue/Dashboard trên DB dùng một lần.
- `scripts/generate_architecture_drawio.py`, `generate_architecture_excalidraw.mjs` — Sinh sơ đồ kiến trúc trong `docs/`.

## 15. references/ và web/ (tài liệu phụ)

- `references/papers_20260926_end_to_end_risk_ml.md` — Danh sách bài báo đã kiểm chứng cho risk ML.
- `references/research_20260926_production_ml_books_blogs.md` — Sách và tài liệu kỹ thuật production ML.
- `references/search_20260926_olist_dataset_schema.md` — Ghi chú schema Olist.
- `web/BaoCao_LaTeX/` — Báo cáo môn Phát triển Web cùng hệ thống; `web/BaoCao_LaTeX/chuong/01-gioi-thieu.tex` có phần giới thiệu viết sẵn, các chương khác ngắn. `tailieu.bib` là bib riêng.
- `web/SoDo/use-case-user-flow.drawio` (+ 3 PNG xem trước) — Use case và user flow Specialist/Manager (theo BRD v3.0, đã cũ).
- `web/Wireframe/*.html|js|css` — Wireframe HTML tĩnh với dữ liệu giả (login, overview, order, actions).
