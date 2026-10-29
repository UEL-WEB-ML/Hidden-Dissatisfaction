# Kế hoạch cải thiện độ chính xác mô hình Hidden Dissatisfaction

## 1. Mục tiêu

Tài liệu này là execution plan để cải thiện khả năng xếp hạng các order có nguy cơ nhận
review 1–2 sao, chủ yếu thông qua data và feature engineering. Plan này bổ sung cho
[`modeling-training-plan.md`](modeling-training-plan.md), không thay đổi các nguyên tắc
evaluation đã được cố định trong ADR-010 đến ADR-014.

Mục tiêu thực nghiệm:

- Baseline development hiện tại: order-level PR-AUC `0.210955`, đạt bởi
  `order_weight:random_forest-depth8-leaf5-v1` trên feature schema
  `p5-item-v2-delivery-product`.
- Stop target: order-level PR-AUC tối thiểu `0.25` trên development protocol đã freeze.
- Không mở sealed final-test để chọn feature, model, hyperparameter hoặc threshold.
- Chỉ giữ một feature group khi có uplift ổn định, hợp lệ tại prediction time và có ý nghĩa
  vận hành.
- Sau khi đạt stop target, dừng mở rộng feature/model, thực hiện stability analysis, khóa
  selection record rồi mới xem xét finalization theo release gate riêng.

Order-level PR-AUC là metric chính vì target và workflow đều ở grain order. Brier score,
recall@budget và calibration là metric phụ; accuracy tại threshold `0.5` không được dùng để
chọn model do target mất cân bằng.

## 2. Những nguyên tắc không được phá vỡ

### 2.1. Prediction-time contract

Mỗi feature phải có thể tính được tại `prediction_at = order_delivered_customer_date`.
Feature của order hiện tại không được dùng:

- review score, review text, review creation/answer time;
- outcome hoặc thao tác CSKH xảy ra sau delivery;
- statistic được tính từ order có `prediction_at` trong tương lai;
- statistic lịch sử có review chưa được tạo trước `prediction_at`;
- aggregate được fit trên toàn bộ dataset trước khi temporal split.

### 2.2. Quy tắc point-in-time cho lịch sử có nhãn

Với order hiện tại `i`, một historical order `j` chỉ được dùng khi đồng thời:

```text
prediction_at(j) < prediction_at(i)
review_created_at(j) < prediction_at(i)
order_id(j) != order_id(i)
```

Điều kiện thứ hai rất quan trọng: tại thời điểm dự đoán order `i`, nhãn của order `j` chỉ
được xem là đã biết nếu review của `j` thực sự đã xuất hiện. Không được dùng chỉ vì order
`j` đã delivery trước đó.

### 2.3. Grain và split

- Dataset canonical vẫn là một dòng/product item.
- Label, temporal partition và metric chính vẫn ở order grain.
- Mọi item thuộc cùng một order phải nằm trong cùng partition.
- Feature order-level được lặp lại trên item chỉ khi nhất quán trong order.
- `order_aggregate` là challenger, không mặc định thay thế item regimes vì v5 CPU precheck
  chưa thắng baseline.
- Các boundary trong `configs/experiment.toml` phải được giữ nguyên trong toàn bộ chương
  trình feature engineering này.

### 2.4. Experiment discipline

- Mỗi experiment chỉ thêm hoặc bỏ một feature group đã định nghĩa trước.
- Không đổi đồng thời feature group, split, metric và candidate set.
- Mỗi run phải ghi protocol version, feature schema version, source hash, seed, regime,
  estimator, calibration và metric theo fold.
- GPU CatBoost có thể nondeterministic nhẹ; quyết định không dựa trên một run đơn lẻ khi
  uplift nhỏ.
- Không dùng correlation trên toàn dataset để lọc feature trước split.

## 3. Thứ tự ưu tiên tổng thể

| Ưu tiên | Strategy | Kỳ vọng | Rủi ro chính | Trạng thái |
|---|---|---:|---|---|
| S0 | Khóa baseline và diagnostics | Bắt buộc | So sánh sai protocol | Cần xác nhận GPU v5 |
| S1 | Target history có Bayesian smoothing | Cao nhất | Temporal/label leakage | Làm đầu tiên |
| S2 | Seller operational history | Cao | Sai point-in-time | Sau S1 |
| S3 | Logistics và geography | Trung bình–cao | Geocode thiếu/nhiễu | Sau S2 |
| S4 | Order complexity và concentration | Trung bình | Trùng lặp feature | Có thể song song S3 |
| S5 | Payment behavior | Trung bình | Cardinality nhỏ, signal yếu | Sau S4 |
| S6 | Product morphology/content | Thấp–trung bình | Missingness | Sau S5 |
| S7 | Calendar và temporal drift | Trung bình | Overfit seasonality | Sau S2 |
| S8 | Missingness/support indicators | Thấp nhưng rẻ | Redundancy | Thêm cùng từng group |
| S9 | Interactions và ratios | Trung bình | Feature explosion | Chỉ sau feature gốc |
| S10 | Feature selection và ensemble | Trung bình | Selection bias | Sau ablation |

## 4. S0 — Khóa baseline và dựng bộ diagnostics

### Mục tiêu

Tạo một mốc so sánh có thể tái lập trước khi thêm feature mới.

### Công việc

1. Khôi phục GPU/WSL và chạy chính thức protocol
   `p5-v5-order-aggregate-challenger` mà không dùng `--finalize-test`.
2. Lưu selection record riêng cho baseline v5.
3. Tạo một feature inventory gồm:
   - tên feature;
   - grain;
   - source table;
   - thời điểm feature trở nên biết được;
   - null rate;
   - cardinality hoặc phân vị;
   - feature group;
   - leakage classification.
4. Tạo diagnostics trên từng development fold:
   - order count và positive prevalence;
   - null rate theo thời gian;
   - PSI hoặc drift summary giữa các fold;
   - univariate temporal PR-AUC;
   - Spearman cho numeric-numeric;
   - Cramér's V cho categorical-categorical;
   - mutual information chỉ fit trên training portion;
   - grouped permutation importance trên validation portion.

### Quy tắc dùng correlation

Correlation chỉ dùng để phát hiện redundancy, lỗi dữ liệu và gợi ý interaction. Không bỏ
feature chỉ vì Pearson correlation với target thấp vì tree model có thể học quan hệ phi tuyến,
threshold và interaction. Không giữ feature chỉ vì correlation cao vì đó có thể là leakage.

### Deliverables

- `reports/experiments/p5-v5-baseline-*.json`;
- `reports/feature-diagnostics/p5-v5-feature-inventory.csv`;
- `reports/feature-diagnostics/p5-v5-temporal-diagnostics.json`;
- baseline table theo fold và regime.

### Gate hoàn thành

- Cùng một source snapshot và config cho tất cả experiment sau đó.
- Zero order overlap giữa partitions.
- Sealed test chưa được đọc hoặc chấm điểm.
- Baseline official được ghi lại trước khi sửa schema tiếp theo.

## 5. S1 — Target history với Bayesian smoothing

Đây là strategy ưu tiên cao nhất. Seller/category performance trong quá khứ có khả năng mang
signal mạnh hơn average review score thô, nhưng phải được tính point-in-time tuyệt đối.

### 5.1. Feature đề xuất

Cho mỗi entity `e` và order hiện tại tại thời điểm `t`:

```text
n(e,t)       = số historical orders hợp lệ của entity e trước t
k(e,t)       = số historical orders có negative = 1
p_global(t)  = negative rate toàn cục từ các label đã quan sát trước t
smoothed_negative_rate(e,t)
             = (k(e,t) + m * p_global(t)) / (n(e,t) + m)
```

`m` là prior strength; thử tập nhỏ `[10, 25, 50]` bằng development folds, không tune trên
final-test.

Thêm các feature group sau:

| Entity/window | Features |
|---|---|
| Seller/all history | count, negative count, smoothed negative rate, score mean, support flag |
| Seller/30d, 90d | count, smoothed negative rate, score mean |
| Category/all history | count, negative count, smoothed negative rate, support flag |
| Category/30d, 90d | count, smoothed negative rate |
| Seller × category | count, smoothed negative rate, low-support flag |
| Global history | expanding negative rate, 30d negative rate, 90d negative rate |

Không tạo raw target encoding cho `seller_id` hoặc `product_category` bằng cách group trên toàn
dataset. Mọi statistic phải được tính riêng cho từng event time.

### 5.2. Support và fallback

- `n = 0`: dùng `p_global(t)` và bật `cold_start_flag = 1`.
- `1 <= n < 5`: vẫn dùng smoothed rate, bật `low_support_flag = 1`.
- `n >= 5`: dùng smoothed rate, `low_support_flag = 0`.
- Không set rate thành null chỉ vì support thấp; model cần cả posterior estimate và support.
- Luôn cung cấp `log1p(n)` để model phân biệt độ tin cậy.

### 5.3. Implementation

1. Tạo intermediate event table một dòng/order/entity để multi-item order không bị đếm lặp.
2. Giữ strict conditions trong mục 2.2 tại SQL join.
3. Tính expanding global prior tại đúng event time.
4. Tạo window 30 và 90 ngày dựa trên `prediction_at`, không dựa trên row position.
5. Version hóa thành `p5-item-v3-target-history`.
6. Bổ sung singular dbt tests cho:
   - same-time event bị loại;
   - review xuất hiện sau cutoff bị loại;
   - multi-item order chỉ đếm một lần/entity;
   - current order không tự đóng góp vào history;
   - zero-history fallback đúng;
   - window boundary đúng 30/90 ngày.

### 5.4. Ablation bắt buộc

Chạy lần lượt:

1. Baseline v5.
2. Baseline + seller smoothed history.
3. Baseline + category smoothed history.
4. Baseline + seller + category.
5. Bước 4 + 30/90d windows.
6. Bước 5 + seller × category, chỉ khi support đủ.

### 5.5. Trạng thái implementation

Repository implementation hoàn thành ngày 2026-10-28:

- schema `p5-item-v3-target-history` và model `int_p5_target_history` đã được nối vào Gold mart;
- prior strength mặc định là `25`, có thể override bằng dbt var;
- dbt unit/data tests bảo vệ strict cutoff, event deduplication, zero-history fallback và
  boundary 30/90 ngày;
- training config dùng feature groups tường minh, mặc định chỉ chạy `baseline`;
- `scripts/run-s1-ablations.sh` chạy development-only E00–E04 và không có đường dẫn
  `--finalize-test`.

Empirical status vẫn là pending cho đến khi PostgreSQL/dbt build tạo lại Parquet v3 và các report
E00–E04 tồn tại. Không được đánh dấu feature là retained chỉ dựa trên implementation hoặc synthetic
tests.

Không gộp tất cả ngay từ đầu vì sẽ không biết uplift đến từ đâu.

### Gate giữ feature

Giữ feature group nếu:

- mean rolling-fold order PR-AUC tăng ít nhất `0.005`; hoặc
- tăng ít nhất `0.003` và đồng thời Brier/recall@5% cải thiện rõ;
- không làm giảm PR-AUC quá `0.005` ở bất kỳ fold nào mà không có giải thích drift hợp lý;
- permutation importance không âm ổn định;
- không vi phạm point-in-time tests.

Uplift nhỏ hơn các mức trên được xem là chưa đủ mạnh để bù complexity, trừ khi feature đó rất
rẻ và tăng stability qua tất cả folds.

## 6. S2 — Seller operational history không phụ thuộc review

Strategy này bổ sung signal vận hành ngay cả khi review đến chậm hoặc seller chưa đủ labeled
history. Chỉ dùng dữ liệu order/delivery đã xảy ra trước order hiện tại.

### Feature đề xuất

| Nhóm | Feature |
|---|---|
| Tenure | days since seller first observed order, days since first delivered order |
| Volume | prior order count 30d/90d/all, prior item count, active days |
| Speed | mean/median approval-to-carrier, carrier-to-delivery, purchase-to-delivery |
| Reliability | prior late-shipping rate, prior late-delivery rate trên toàn population khả dụng |
| Variability | std/IQR delivery duration, std freight/value ratio |
| Recency | days since seller previous order/delivery |
| Trend | 30d rate minus 90d rate, recent duration minus long-run duration |

Vì primary cohort hiện chỉ gồm on-time/early deliveries, prior late-delivery rate phải được tính
từ population vận hành rộng hơn trước khi lọc primary modeling cohort. Không được suy ra rate này
từ cohort đã loại late orders.

### Feature formulas quan trọng

```text
seller_volume_velocity_30d = prior_order_count_30d / 30
seller_recent_vs_long_delivery_delta
  = mean_delivery_days_30d - mean_delivery_days_all
seller_delivery_cv
  = std_delivery_days_all / nullif(mean_delivery_days_all, 0)
seller_cold_start_flag = 1[n_prior_orders = 0]
```

### Tests

- Historical order phải có event outcome biết được trước `prediction_at`.
- Current order không đóng góp vào seller history.
- Multi-item order chỉ đóng góp một order vào order count.
- Null timestamps không được biến thành duration bằng 0.
- Feature từ wider operational population không kéo review fields vào model.

### Ablation

1. Tenure + volume.
2. Speed + variability.
3. Reliability.
4. Trend windows.
5. Tất cả seller operational features đã qua gate.

### Trạng thái S2

Đã chạy development ablation ngày 2026-10-28 trên schema
`p5-item-v4-seller-operations`. Chỉ nhóm speed + variability được retain có điều kiện
(rolling order PR-AUC `0.140681`, uplift `+0.004355`, Brier cải thiện và cả ba fold đều tăng
PR-AUC). Tenure/volume, reliability và trend bị loại. Chi tiết quyết định nằm tại
`reports/P5-S2-seller-operations-ablation.md`. Sealed final test chưa được chấm điểm.

## 7. S3 — Logistics và geography

### Feature đề xuất

1. Join customer/seller ZIP centroid từ `dim_zip_centroid`.
2. Tính Haversine distance giữa seller và customer.
3. Thêm:
   - `seller_customer_distance_km`;
   - `same_state_flag`;
   - `same_city_flag` nếu chuẩn hóa city đủ tin cậy;
   - `cross_state_flag`;
   - `route_pair = seller_state + customer_state` cho CatBoost native categorical;
   - `route_prior_order_count`;
   - point-in-time route mean/median delivery days;
   - point-in-time route negative rate có smoothing, chỉ sau khi S1 ổn định;
   - `distance_per_delivery_day` chỉ là diagnostic vì delivery duration đã biết tại prediction;
   - missing ZIP/centroid flags.

### Công thức Haversine

```text
d = 2R * asin(sqrt(
      sin²((lat2-lat1)/2)
      + cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)
    ))
```

Với `R = 6371.0088 km`. Clamp input của `asin` về `[0, 1]` để tránh lỗi floating-point.

### Guardrails

- Không dùng raw latitude/longitude nếu chưa chứng minh tốt hơn distance/state features.
- ZIP không map được phải là null + missing flag, không impute thành `(0,0)`.
- Route history phải point-in-time và có support/fallback như S1.
- Cardinality của city/route phải được kiểm tra theo từng fold; rare route cần gộp hoặc để
  native CatBoost xử lý.

### Ablation

1. Distance + same-state + missing flags.
2. Bước 1 + route categorical.
3. Bước 2 + operational route history.
4. Bước 3 + smoothed route target history.

### Trạng thái S3

Đã chạy development ablation ngày 2026-10-28 trên schema `p5-item-v5-geography`.
Distance/state flags và route categorical đều không qua gate; operational route history không
được chạy vì prerequisite thất bại, còn route target history bị bỏ qua do S1 chưa ổn định.
Retained set vẫn là `baseline + seller_operations_speed_variability`. Xem
`reports/P5-S3-geography-ablation.md`.

## 8. S4 — Order complexity và concentration

Order nhiều seller/category hoặc giá trị tập trung vào một item có thể tạo trải nghiệm khác với
order đơn giản. Feature phải được aggregate deterministic trong từng order.

### Feature đề xuất

```text
order_seller_count
order_category_count
order_product_count
order_unique_product_count
order_item_count
order_item_value_total
order_freight_total
order_freight_share = freight_total / nullif(item_value_total, 0)
order_max_item_value_share
order_min_item_value_share
order_price_mean / std / max / min
order_freight_mean / std / max
order_category_hhi = sum(category_value_share²)
order_seller_hhi = sum(seller_value_share²)
multi_item_flag
multi_seller_flag
multi_category_flag
```

HHI gần `1` nghĩa là order tập trung; HHI thấp nghĩa là phân tán. Với item regime, các feature
order-level được lặp nhất quán trên mọi item. Với `order_aggregate`, mỗi feature chỉ xuất hiện một
lần/order.

### Tests

- `seller_count`, `category_count`, `product_count` không lớn hơn `item_count`.
- Tổng item value shares gần `1` khi denominator dương.
- HHI nằm trong `(0, 1]` với order hợp lệ.
- Feature order-level không thay đổi giữa các item cùng order.
- Null category được xử lý thành một bucket rõ ràng, không biến mất khỏi count.

### Ablation

1. Counts + binary flags.
2. Value/freight ratios.
3. Concentration HHI.
4. Distribution statistics.

### Trạng thái S4

Đã triển khai và chạy development ablation ngày 2026-10-28 trên schema
`p5-item-v6-order-composition`. Package counts/ratios/HHI đạt rolling order PR-AUC `0.144470`
(tăng `+0.003789` so với retained S2) và tăng ở cả ba fold; Brier kém hơn `0.001185` nên chỉ
được giữ có điều kiện. Counts đứng riêng và distribution statistics bị loại. Retained set là
`baseline + seller_operations_speed_variability + order_composition_counts +
order_composition_ratios + order_composition_concentration`. Sealed final test chưa được chấm.
Chi tiết nằm tại `reports/P5-S4-order-composition-ablation.md`.

## 9. S5 — Payment behavior

Current schema mới có count, total amount và max installments; cần bổ sung cấu trúc thanh toán.

### Feature đề xuất

- `payment_type_count`;
- one-hot/binary cho `credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`;
- `primary_payment_type`;
- `payment_installments_mean`, `payment_installments_max`;
- `installment_amount = payment_amount / max_installments`;
- `payment_to_order_value_ratio`;
- `voucher_share`, `credit_card_share`;
- `split_payment_flag = payment_count > 1`;
- `mixed_payment_type_flag = payment_type_count > 1`;
- payment value concentration/HHI khi một order có nhiều payment rows.

### Trạng thái S5

Đã triển khai và chạy development ablation ngày 2026-10-28 trên schema
`p5-item-v7-payment-behavior`. Payment structure bị giảm PR-AUC (`-0.003056`); payment
shares/HHI/primary type chỉ tăng `+0.000617` trung bình, giảm ở hai trong ba fold và giảm
selection-holdout PR-AUC. Không có nhóm S5 nào được retain. Sealed final test chưa được chấm.
Chi tiết tại `reports/P5-S5-payment-behavior-ablation.md`.

### Guardrails

- Aggregate payment table về một dòng/order trước khi join item table.
- Không nhân số item rows do payment multiplicity.
- Ratio denominator bằng 0 phải thành null + denominator-zero flag, không thành infinity.
- Payment type rare bucket phải được fit theo training fold nếu có threshold học từ data.

## 10. S6 — Product morphology và content completeness

### Feature đề xuất

```text
product_volume_cm3 = length_cm * height_cm * width_cm
product_density_g_cm3 = weight_g / nullif(product_volume_cm3, 0)
product_max_dimension_cm
product_min_dimension_cm
product_dimension_ratio = max_dimension / nullif(min_dimension, 0)
freight_to_price_ratio = freight_value / nullif(price, 0)
freight_per_kg = freight_value / nullif(weight_g / 1000, 0)
photos_per_100_currency = photos_qty / nullif(price / 100, 0)
product_name_length
product_description_length
product_metadata_missing_count
```

### Guardrails

- Winsorization threshold chỉ fit trên training portion hoặc được cố định theo domain rule.
- Không mặc định coi missing là 0; giữ null và thêm missing indicator.
- Density/dimension outlier phải được report, không âm thầm xóa row.
- Content length là metadata có trước prediction time; review text tuyệt đối không được dùng.

### Trạng thái S6

Đã triển khai và chạy development ablation ngày 2026-10-29 trên schema
`p5-item-v8-product-morphology`. Morphology/freight ratios đứng riêng bị loại (`-0.001873`
PR-AUC), nhưng package morphology + content completeness/missingness đạt `0.146502`
(`+0.002032` so với retained S4), tăng ở cả ba fold và cải thiện Brier `0.003900`. Vì
selection-holdout PR-AUC giảm, package chỉ được retain có điều kiện. Sealed final test chưa được
chấm. Chi tiết tại `reports/P5-S6-product-morphology-ablation.md`.

## 11. S7 — Calendar, recency và drift

### Feature đề xuất

- purchase month, weekday, hour;
- delivery month, weekday;
- days to major shopping periods nếu định nghĩa calendar cố định;
- month-age index từ đầu dataset;
- rolling global negative prevalence 30d/90d;
- rolling order volume 7d/30d;
- seller workload proxy: seller orders active/recent in 7d/30d;
- category recent volume and recent-vs-long-run trend.

### Guardrails

- Calendar mapping phải deterministic, không học từ target.
- Không dùng random split để kiểm tra calendar features.
- Feature month/year có thể học dataset era thay vì behavior; chỉ giữ nếu uplift ổn định trên
  rolling folds và không làm fold cuối suy giảm mạnh.
- Global target prevalence chỉ dùng label đã quan sát trước prediction time.

### Trạng thái S7

Đã triển khai và chạy development ablation ngày 2026-10-29 trên schema
`p5-item-v9-temporal-features`. Calendar giảm rolling PR-AUC `0.000440` và suy giảm rõ ở fold
cuối; thêm strict prior-volume giảm thêm `0.003703`. Không nhóm S7 nào được retain, dù Brier tốt
hơn, vì PR-AUC là metric chọn chính. Sealed final test chưa được chấm. Chi tiết tại
`reports/P5-S7-temporal-features-ablation.md`.

## 12. S8 — Missingness, support và data quality

Missingness có thể là signal về quy trình nhập liệu nhưng cần diễn giải thận trọng.

Thêm indicator cho từng nhóm:

- product dimensions missing;
- product content missing;
- carrier timestamp missing;
- seller/customer centroid missing;
- category missing;
- payment anomaly/missing;
- seller/category/route cold start;
- seller/category/route low support;
- tổng số field thiếu theo row và theo order.

Mỗi numeric history feature phải đi cùng support count hoặc support class. Không cho model nhìn
một smoothed rate mà không biết rate đó đến từ 0, 2 hay 500 observations.

### Trạng thái S8

Đã chạy development ablation ngày 2026-10-29 trên schema `p5-item-v10-data-quality`.
Category/payment/customer/carrier missingness flags và missing-count giảm rolling PR-AUC `0.002426`,
làm Brier và selection holdout xấu hơn; nhóm bị loại. Các indicator morphology/content đã được
retain từ S6 không bị ảnh hưởng. Sealed final test chưa được chấm. Chi tiết tại
`reports/P5-S8-data-quality-ablation.md`.

## 13. S9 — Interactions và ratios có kiểm soát

Chỉ tạo interaction sau khi cả hai feature gốc đã qua ablation gate. Ưu tiên interaction có giả
thuyết nghiệp vụ rõ:

```text
distance_km × freight_to_price_ratio
distance_km / delivery_days
seller_negative_rate × seller_support_log1p
category_negative_rate × item_value_share
seller_recent_volume × seller_recent_delivery_delta
order_seller_count × order_category_count
product_weight × distance_km
estimated_delivery_buffer_days / purchase_to_delivery_days
```

Không polynomial-expand toàn bộ feature matrix. Mỗi interaction group tối đa khoảng 5–10 biến,
được kiểm tra bằng group ablation. Tree model đã tự học nhiều interaction; explicit interaction chỉ
giữ khi cải thiện linear model hoặc tăng stability/interpretability.

### Trạng thái S9

Đã chạy development ablation ngày 2026-10-29 trên schema `p5-item-v11-interactions`. Bốn
hypothesis-led interaction giảm rolling PR-AUC `0.000458` và giảm ở hai folds; nhóm bị loại dù
Brier và selection holdout tốt hơn nhẹ. Sealed final test chưa được chấm. Chi tiết tại
`reports/P5-S9-interactions-ablation.md`.

## 14. S10 — Feature selection và model/ensemble sau feature engineering

### 14.1. Selection pipeline

Sau khi từng group qua gate:

1. Loại constant và near-constant features theo training fold.
2. Kiểm tra duplicate/near-duplicate features.
3. Cluster numeric features có `|Spearman| >= 0.95`; không tự động bỏ mà đánh giá theo group.
4. Chạy grouped permutation importance trên từng validation fold.
5. Chạy leave-one-group-out ablation.
6. Dùng SHAP để kiểm tra direction và stability, không dùng SHAP như bằng chứng nhân quả.
7. Tạo compact feature set nếu hiệu năng không giảm quá `0.002` PR-AUC so với full set.

### 14.2. Model strategy

Chỉ sau khi feature set ổn định:

- tune bounded CatBoost depth, learning rate và regularization trên GPU;
- so sánh native categorical với encoded categorical;
- cân nhắc LightGBM/XGBoost chỉ bằng một ADR mới và candidate set bounded;
- thử weighted average/blending của hai model có error diversity rõ ràng;
- fit blend weight trên development calibration/selection partition, không trên sealed test;
- calibration vẫn là bước độc lập sau model selection.

Ensemble chỉ được giữ nếu tăng order PR-AUC ít nhất `0.005` hoặc tăng recall@5% đáng kể mà không
làm Brier xấu rõ rệt. Không ensemble chỉ để có architecture phức tạp hơn.

### Trạng thái S10

Đã chạy leave-one-group-out ngày 2026-10-29. Bỏ seller speed/variability, order composition,
hoặc product morphology/content lần lượt giảm rolling PR-AUC `0.004152`, `0.005027`, và
`0.002032`; tất cả vượt compact-set tolerance `0.002`. Compact set vì vậy giữ nguyên full retained
set. Sau khi GPU được khôi phục, bounded CatBoost tuning chọn depth 6 trong candidate set với
rolling PR-AUC `0.145813` và selection-holdout PR-AUC `0.223873`. Candidate này không thay
Random Forest retained (`0.146502`) vì metric chính rolling giảm `0.000689`; holdout đơn lẻ không
được dùng để đảo quyết định. Không blend vì chưa có candidate thứ hai đạt uplift ổn định `0.005`.
Historical final-test không được mở lại; P12 yêu cầu replacement holdout thật sự chưa từng xem cho
confirmatory evaluation. Chi tiết tại `reports/P5-S10-feature-selection.md`.

## 15. Ma trận experiment đề xuất

| Run | Feature set | So với | Mục đích |
|---|---|---|---|
| E00 | v5 baseline | — | Khóa mốc official |
| E01 | E00 + seller smoothed target history | E00 | Signal seller label history |
| E02 | E00 + category smoothed target history | E00 | Signal category label history |
| E03 | E00 + retained S1 groups | E00/E01/E02 | Interaction seller/category |
| E04 | E03 + 30/90d target windows | E03 | Recency/trend |
| E05 | E04 + seller tenure/volume | E04 | Cold start và activity |
| E06 | E05 + seller speed/reliability | E05 | Operational quality |
| E07 | E06 + distance/same-state | E06 | Geography |
| E08 | E07 + route history | E07 | Logistics route |
| E09 | E08 + order complexity | E08 | Multi-item/seller/category |
| E10 | E09 + payment behavior | E09 | Payment structure |
| E11 | E10 + product morphology | E10 | Physical/content signal |
| E12 | E11 + calendar/drift | E11 | Temporal changes |
| E13 | E12 + selected interactions | E12 | Conditional effects |
| E14 | Compact feature selection | E13 | Giảm noise/complexity |
| E15 | Bounded model tuning/blend | E14 | Khai thác feature set cuối |

Nếu một run không qua gate, run tiếp theo phải xuất phát từ last retained set, không mặc định kế
thừa feature vừa thất bại.

## 16. Tiêu chí đánh giá và quyết định

### Metric hierarchy

1. Mean rolling-origin order max-v1 PR-AUC.
2. Worst-fold order PR-AUC và độ lệch giữa folds.
3. Order Brier score sau calibration.
4. Recall@5%, recall@10%, recall@20%.
5. Low-review order value captured tại cùng budgets.
6. Item-level metrics chỉ dùng diagnostic.

### Phân loại kết quả experiment

| Mức | Điều kiện gợi ý | Quyết định |
|---|---|---|
| Fail | Uplift âm hoặc leakage/test fail | Bỏ feature group |
| Inconclusive | Uplift `< 0.003` hoặc không ổn định | Không merge vào retained set; điều tra |
| Useful | Uplift `0.003–0.010`, ổn định và metric phụ không xấu | Giữ có điều kiện |
| Strong | Uplift `> 0.010` và đa số folds tăng | Giữ |
| Stop target | PR-AUC `>= 0.25`, stability/calibration đạt | Dừng tuning mở rộng |

Threshold trên là engineering gate cho development, không phải confidence interval thống kê. Khi
hai model gần nhau, dùng paired order-cluster bootstrap trên cùng prediction rows để định lượng
uncertainty; tuyệt đối không resample item độc lập.

### Stability gate trước khi stop

Khi model đạt `>= 0.25`:

1. Chạy lại GPU tối thiểu 3 lần với cùng config nếu candidate có nondeterminism.
2. Xác nhận median PR-AUC vẫn `>= 0.25` hoặc không thấp hơn target quá `0.002`.
3. Xác nhận không fold nào collapse so với retained baseline.
4. Chạy subgroup diagnostics theo month, category, seller support và geography.
5. Khóa schema, candidate, calibration, regime và threshold policy.
6. Ghi ADR mới cho selected development model.
7. Chỉ sau release approval mới chạy sealed final-test đúng một lần.

## 17. Cấu trúc implementation dự kiến

### dbt

- `dbt/models/intermediate/int_p5_target_history.sql`
- `dbt/models/intermediate/int_p5_seller_operations.sql`
- `dbt/models/intermediate/int_p5_route_features.sql`
- `dbt/models/intermediate/int_p5_order_composition.sql`
- `dbt/models/intermediate/int_p5_payment_features.sql`
- `dbt/models/intermediate/int_p5_product_features.sql`
- unit fixtures tương ứng trong `dbt/models/intermediate/*_unit.yml`
- join retained features vào `dbt/models/gold/ml_modelling_items.sql`

Tên chính xác có thể điều chỉnh theo convention hiện tại, nhưng mỗi model phải có một ownership
rõ và không tạo một SQL file duy nhất chứa toàn bộ feature logic.

### Python

- cập nhật feature lists và schema version trong
  `src/hidden_dissatisfaction/modeling/schema.py`;
- cập nhật database reader/export contract khi thêm cột;
- thêm diagnostics module thay vì nhét analysis vào notebook;
- giữ preprocessing trong estimator pipeline để fit riêng từng fold;
- thêm group-ablation configuration để run có thể tái lập;
- notebook chỉ render artifact, không tự tính feature hoặc train lại model.

### Versioning

Mỗi wave được giữ lại phải tăng:

- `feature_schema_version`;
- `feature_set_version`;
- `protocol_version` nếu candidate/regime/evaluation logic thay đổi;
- ADR nếu thay đổi protocol hoặc selected model boundary.

Feature experiment bị loại không cần trở thành canonical schema; có thể tồn tại trên branch hoặc
config experiment riêng nhưng kết quả phải được ghi lại để tránh thử lại vô thức.

## 18. Test plan

### Data/dbt tests

- uniqueness của `product_item_id`;
- consistency target/prediction/features trong cùng order;
- point-in-time history boundaries;
- không self-history;
- không duplicate do payment/review/item joins;
- valid range cho rate, share, HHI và distance;
- null/missing flags nhất quán;
- feature row count không đổi ngoài thay đổi được giải thích;
- zero overlap giữa temporal partitions.

### Python unit tests

- schema từ chối unknown/forbidden features;
- regime aggregation đúng cho feature mới;
- preprocessing không fit từ validation data;
- diagnostics chỉ dùng declared partition;
- grouped permutation/ablation giữ order grouping;
- config parsing cho feature groups;
- train synthetic end-to-end vẫn chạy cho mọi regime.

### Regression tests

- Baseline schema v2 vẫn đọc được nếu migration policy yêu cầu backward compatibility.
- Feature schema mới cho kết quả deterministic ở CPU components.
- Order count và target prevalence không thay đổi chỉ vì thêm feature.
- Không có review-derived column trong runtime model input.

## 19. Runbook cho mỗi wave

Giả sử Docker/PostgreSQL đã healthy và source run vẫn là
`6f13bf55-5ce3-4a58-807e-e1c31ff76eaa`:

1. Sửa/tạo dbt model và tests cho đúng một feature group.
2. Chạy dbt build không gồm `release_only`:

   ```bash
   docker compose --profile jobs run --rm warehouse \
     dbt build --exclude tag:release_only --project-dir dbt --profiles-dir dbt
   ```

3. Chạy P4 release verification trước khi promote dataset.
4. Export lại parquet và manifest bằng `export-modelling-items`, khai báo schema version mới.
5. Chạy schema/unit/quality tests.
6. Chạy development training trên GPU, ví dụ:

   ```bash
   .venv/bin/hidden-dissatisfaction train \
     --data data/processed/modelling_items.parquet \
     --config configs/experiment.toml \
     --output-root . \
     --selection-record artifacts/checkpoints/<experiment>-selection.json \
     > /tmp/<experiment>-report.json
   ```

7. Không thêm `--finalize-test`.
8. So sánh report mới với last retained experiment theo metric hierarchy.
9. Ghi decision `retain`, `reject` hoặc `inconclusive` cùng lý do.
10. Chỉ bắt đầu wave tiếp theo sau khi schema/report của wave hiện tại đã được version hóa.

Khi GPU chỉ truy cập được trong Ubuntu WSL, chạy cùng command qua:

```bash
wsl -d Ubuntu -- bash -lc \
  'cd /home/hatca/projects/Hidden-Dissatisfaction && <training-command>'
```

## 20. Lịch thực thi gợi ý

### Ngày 1 — Baseline và S1 foundation

- Khôi phục GPU/WSL.
- Chạy E00 official.
- Tạo feature inventory/diagnostics.
- Implement point-in-time negative counts và global prior.
- Viết dbt unit tests trước khi train.

### Ngày 2 — S1 ablations

- E01 seller history.
- E02 category history.
- E03 combined retained groups.
- E04 30/90d windows.
- Quyết định prior strength và retained S1 set.

### Ngày 3 — S2 seller operations

- Implement tenure/volume/speed/reliability.
- Chạy E05/E06.
- Phân tích cold-start và low-support subgroups.

### Ngày 4 — S3/S4

- Implement distance/route features.
- Implement order complexity/concentration.
- Chạy E07–E09.

### Ngày 5 — S5/S6/S7

- Payment behavior.
- Product morphology/content.
- Calendar/drift.
- Chạy E10–E12 và loại feature groups yếu.

### Ngày 6 — S9/S10

- Chỉ thêm interaction có hypothesis.
- Grouped permutation + leave-one-group-out ablation.
- Tạo compact feature set.
- Bounded GPU model tuning/blending.

### Ngày 7 — Stability và lock

- Repeat runs cho GPU candidate tốt nhất.
- Bootstrap comparison và subgroup analysis.
- Nếu đạt `0.25`, dừng tuning và tạo ADR lock.
- Nếu chưa đạt, viết failure analysis trước khi mở rộng model/data scope.

Thời gian trên là thứ tự công việc, không phải deadline cứng; một wave chỉ đóng khi qua test và
decision gate.

## 21. Khi chưa đạt 0.25 sau E15

Không tiếp tục thêm feature ngẫu nhiên. Thực hiện failure analysis:

1. Kiểm tra label noise do order-level review kế thừa xuống item.
2. So sánh direct order model và item-to-order aggregation theo cùng feature set.
3. Phân tích upper-bound signal theo seller/category support groups.
4. Kiểm tra concept drift và độ khác nhau giữa temporal folds.
5. Kiểm tra review-observation selection bias; cân nhắc two-stage sensitivity model theo
   `research-design.md`, nhưng không đổi primary estimand âm thầm.
6. Đánh giá external/new data chỉ khi có contract và prediction-time availability rõ ràng.
7. Viết ADR trước khi mở candidate family, đổi cohort, đổi target hoặc đổi temporal boundary.

Không hạ tiêu chí bằng cách dùng random split, xem sealed test nhiều lần, target-encode toàn
dataset hoặc đưa post-review fields vào model.

## 22. Definition of Done

Plan cải thiện accuracy được xem là hoàn thành khi một trong hai điều kiện xảy ra:

### Thành công

- Development order PR-AUC đạt `>= 0.25` qua stability gate;
- selected feature set có point-in-time tests và ablation evidence;
- calibration/recall@budget không suy giảm bất hợp lý;
- schema, config, artifact, report và ADR đã version hóa;
- sealed final-test vẫn nguyên vẹn cho đến release gate.

### Dừng có chủ đích

- Tất cả strategy ưu tiên cao đã được ablate đúng protocol nhưng không đạt target;
- failure analysis chỉ ra giới hạn từ label/data thay vì thiếu model tuning;
- mọi kết quả âm được ghi lại;
- thay đổi tiếp theo cần new data, target hoặc research design và phải có quyết định mới.

### Trạng thái đóng plan — 2026-10-29

Plan đã hoàn thành theo nhánh **dừng có chủ đích**. Mười phase S1–S10 và bounded GPU tuning đã
được chạy; retained Random Forest đạt rolling order PR-AUC `0.146502`, chưa đạt target `0.25`.
Failure analysis nằm tại `reports/P5-accuracy-failure-analysis.md`, còn bản tổng hợp dùng cho môn
học nằm tại `reports/P5-accuracy-coursework-summary.md`. Confirmatory final evaluation vẫn bị P12
block cho đến khi có replacement holdout thật sự chưa từng xem.
