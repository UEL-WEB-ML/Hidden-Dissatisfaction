---
title: "Report: Bối cảnh, khoảng trống và câu hỏi nghiên cứu về bất mãn ẩn trên Olist"
created: 2026-09-26
sources: ["School/ML/Lược khảo.md"]
filed-back: true
---

# Bối cảnh, khoảng trống và câu hỏi nghiên cứu về bất mãn ẩn trên Olist

## Executive Summary

Các nghiên cứu đã cho thấy hiệu suất logistics, đặc biệt là giao trễ, có liên hệ mạnh với đánh giá tiêu cực, hành vi mua lại và doanh số của người bán. Tuy nhiên, giao đúng hạn không đồng nghĩa với hài lòng. Ma trận lược khảo chỉ ra một nhóm quan trọng nhưng ít được nghiên cứu trực tiếp: những đơn đã giao đúng hoặc sớm nhưng vẫn nhận review 1–2 sao. Nhóm này có thể phản ánh các nguyên nhân ngoài trễ giao như chất lượng sản phẩm hoặc seller, phí vận chuyển, đơn nhiều món hoặc nhiều seller, giao tách đợt, sai lệch kỳ vọng và các ma sát dịch vụ khác.

Khoảng trống trung tâm không đơn thuần là thiếu một mô hình có accuracy cao hơn. Khoảng trống nằm ở việc chưa có một quy trình chấm điểm product item và tổng hợp thành order risk đồng thời đáp ứng năm yêu cầu: đúng mốc thông tin trước review, đánh giá theo thời gian ở cấp order, chú trọng lớp thiểu số và hiệu chỉnh xác suất, xử lý review cấp order như nhãn yếu kế thừa bởi item, và chứng minh giá trị ưu tiên dưới ngân sách hữu hạn so với các quy tắc đơn giản. Dữ liệu Olist quan sát không cho phép suy ra hành động chăm sóc nào gây ra cải thiện, nên nghiên cứu chỉ nên tuyên bố khả năng chẩn đoán và ưu tiên case, không tuyên bố hiệu quả nhân quả của voucher, hoàn tiền hay liên hệ khách hàng.

## 1. Bối cảnh nghiên cứu

### 1.1. Từ chất lượng logistics đến sự hài lòng và giá trị kinh doanh

Literature hiện có thiết lập ba mắt xích. Thứ nhất, hiệu suất giao hàng ảnh hưởng đến rating: giao trễ bị phạt mạnh hơn mức giao sớm được thưởng, và thời gian giao dài vẫn có thể làm giảm rating ngay cả khi đơn không bị xem là trễ (Ravula, 2023; Deshpande & Pendem, 2023). Thứ hai, trải nghiệm logistics không chỉ ảnh hưởng đến rating mà còn liên hệ với xác suất mua và doanh số seller (Deshpande & Pendem, 2023). Thứ ba, rating hoặc satisfaction không bao quát toàn bộ hành vi tương lai; chất lượng và giá giao hàng có thể tác động trực tiếp đến retention, còn giao nhanh bằng cách tách đơn có thể làm giảm mua lại do bất tiện và quan ngại môi trường (Rao et al., 2011; Brylla & Walsh, 2022).

Do đó, dự báo review thấp có ý nghĩa quản trị, nhưng review thấp không phải là đại diện hoàn chỉnh cho churn, retention hay lợi nhuận. Item score là tín hiệu rủi ro trong bối cảnh sản phẩm; `max-v1` chuyển các tín hiệu đó thành risk score cấp đơn cho workflow.

### 1.2. Giao trễ là tín hiệu mạnh nhưng tạo ra điểm mù

Các mô hình trên Olist thường đạt hiệu năng cao hơn khi có thông tin giai đoạn giao hàng, vì biến trễ so với ngày dự kiến và thời gian giao là các predictor mạnh. Madane và Azeroual (2026) cho thấy phần lớn rủi ro dự đoán trong mô hình của họ đến từ yếu tố vận hành, nhưng cách đánh giá “giá trị cứu vãn được” chỉ tính những đơn vừa bị chê vừa giao trễ. Theo ghi chú phân tích trong ma trận, 67,5% đơn bị chê trên Olist lại được giao đúng hạn; nếu con số này được tái lập từ dữ liệu, đây là một quần thể lớn bị chính sách delay-centric bỏ sót.

Các nghiên cứu giải thích cũng cho thấy “đúng hạn” không đồng nghĩa “không có ma sát”. Giao sớm chỉ được thưởng nhẹ; thời gian giao tuyệt đối vẫn quan trọng; đơn tách đợt có thể triệt tiêu lợi ích của giao nhanh. Vì vậy, sau khi loại bỏ tín hiệu giao trễ, vẫn còn một bài toán hợp lệ: nhận diện rủi ro bất mãn phát sinh từ cấu trúc đơn hàng, seller, sản phẩm, phí vận chuyển, thời gian giao tuyệt đối và sai lệch kỳ vọng.

### 1.3. Dự báo satisfaction hiện tại chưa phù hợp với triển khai chủ động

Các nghiên cứu phân loại satisfaction đã so sánh nhiều mô hình ML/DL, nhưng một số thiết kế chưa mô phỏng triển khai thực tế. Orman (2026) dùng chia train/test ngẫu nhiên và nhiều thông tin cuối quá trình; mô hình tốt nhất vẫn chỉ đạt recall 14,35% cho lớp không hài lòng. Nghiên cứu so sánh ML và deep learning khác báo accuracy cao nhưng chưa làm rõ temporal validation, calibration, chi phí sai lầm và leakage. Những kết quả này cho thấy mô hình tổng thể có thể trông tốt trong khi gần như không phát hiện được lớp cần can thiệp.

Một thiết kế phù hợp hơn phải xác định rõ prediction time. Với đề tài này, mốc khả thi nhất là ngay sau khi hệ thống xác nhận đơn đã giao đúng hoặc sớm và trước khi khách gửi review. Tại mốc đó, mô hình có thể dùng thông tin đơn hàng, seller, sản phẩm, thanh toán, địa lý, phí vận chuyển, độ phức tạp đơn và thời gian giao đã quan sát; không được dùng review text, review timestamp hoặc biến phát sinh sau review.

### 1.4. Mất cân bằng lớp và xác suất có thể hành động

Lớp review 1–2 sao là lớp thiểu số. Literature không ủng hộ việc mặc định áp dụng SMOTE. Elor và Averbuch-Elor (2022) cho thấy các bộ phân loại boosting mạnh thường không hưởng lợi từ oversampling; van den Goorbergh et al. (2022) cho thấy resampling có thể làm xác suất dự báo bị phóng đại và sai hiệu chỉnh. SPARC cũng phê bình giả định đồng nhất nội lớp của SMOTE trong hành vi khách hàng đa chế độ.

Vì đầu ra được dùng để xếp hạng case, calibration quan trọng không kém discrimination. Thiết kế nên bắt đầu bằng mô hình không resample, class weight hoặc tối ưu ngưỡng; báo cáo PR-AUC, recall/precision của lớp 1–2 sao, Brier score và calibration curve; chỉ dùng resampling như một ablation có hiệu chỉnh lại xác suất.

### 1.5. Review là nhãn có chọn lọc

Người mua tự chọn có viết review hay không, nên tập review không nhất thiết đại diện ngẫu nhiên cho toàn bộ đơn. Các nghiên cứu về review self-selection và phản hồi đa phương thức đều cảnh báo rằng không thể mặc định đơn không review là đơn hài lòng. Do đó, outcome chính nên được diễn đạt là “review 1–2 sao trong số đơn có review”, không phải “khách hàng không hài lòng trong toàn bộ đơn hàng”.

Một phân tích bổ sung có thể tách hai quá trình: xác suất có review và xác suất review thấp khi review được quan sát. Cách này không xóa selection bias, nhưng làm rõ phạm vi suy luận và kiểm tra xem mô hình đang dự báo bất mãn hay chỉ dự báo xu hướng lên tiếng.

### 1.6. Dự báo rủi ro khác với tác động của can thiệp

Các nghiên cứu retention và churn cho thấy nhóm rủi ro cao không nhất thiết là nhóm phản ứng tốt nhất với can thiệp. Uplift hoặc lift cần dữ liệu treatment ngẫu nhiên; Olist không có dữ liệu như vậy. Vì thế, risk score chỉ nên hỗ trợ nhân viên xem xét case. Không thể từ dữ liệu quan sát kết luận khách High Risk phải nhận voucher, refund hoặc một hành động cụ thể.

Đánh giá quyết định vẫn có thể thực hiện ở mức proxy: trong một ngân sách kiểm tra cố định, so sánh số hoặc giá trị đơn review thấp được tìm thấy bởi random, VALUE_ONLY, risk-only và risk × value. Kết quả phải được gọi là decision utility hoặc prioritization utility, không phải uplift hay giá trị thật sự “cứu vãn được”.

## 2. Tổng hợp khoảng trống nghiên cứu

### Gap 1 — Khoảng trống về quần thể nghiên cứu

Phần lớn nghiên cứu và framework ưu tiên tập trung vào giao trễ, trong khi đơn giao đúng/sớm nhưng vẫn bị chê chưa được mô hình hóa như một nhóm mục tiêu riêng. Đây là khoảng trống trực tiếp nhất mà đề tài có thể lấp.

### Gap 2 — Khoảng trống về mốc dự báo và leakage

Các nghiên cứu satisfaction hiện có dùng random split hoặc feature chỉ có ở cuối quy trình, nên chưa trả lời câu hỏi liệu có thể phát hiện bất mãn trước review trong điều kiện triển khai thực tế. Thiếu một thiết kế time-safe với cutoff rõ ràng tại thời điểm xác nhận giao hàng.

### Gap 3 — Khoảng trống về lớp thiểu số và calibration

Accuracy hoặc F1 của lớp đa số che khuất khả năng phát hiện review 1–2 sao. Việc resample có thể cải thiện nhãn dự đoán nhưng làm hỏng xác suất. Chưa có đánh giá đầy đủ kết hợp PR-AUC, minority recall, calibration và threshold/budget analysis cho nhóm đơn đúng hạn.

### Gap 4 — Khoảng trống về selection bias của review

Nhiều nghiên cứu dùng rating như ground truth nhưng không tách quá trình khách có review khỏi nội dung review. Điều này giới hạn khả năng khái quát từ “review thấp được quan sát” sang “bất mãn của mọi khách hàng”.

### Gap 5 — Khoảng trống giữa predictive performance và decision value

Một mô hình có AUC cao chưa chắc ưu tiên case tốt hơn VALUE_ONLY hoặc quy tắc đơn giản. Literature chỉ ra ML không luôn thắng value sorting. Thiếu bằng chứng rằng mô hình rủi ro cho đơn đúng hạn tạo utility gia tăng dưới ngân sách chăm sóc hữu hạn.

### Gap 6 — Khoảng trống nhân quả của hành động service recovery

Olist không quan sát treatment và phản ứng với treatment. Vì vậy, nghiên cứu có thể xác định ai có rủi ro và yếu tố nào liên quan, nhưng không xác định ai có thể được “cứu” hoặc hành động nào hiệu quả. Đây là giới hạn phải được giữ rõ trong claim.

## 3. Phát biểu khoảng trống có thể dùng trong bài

Mặc dù literature đã chứng minh vai trò của hiệu suất giao hàng đối với rating, retention và doanh số, các mô hình hiện có chủ yếu dựa vào tín hiệu giao trễ hoặc đánh giá satisfaction trên toàn bộ đơn hàng bằng thiết kế ngẫu nhiên và metric tổng thể. Điều này để lại một điểm mù đối với những đơn được giao đúng hoặc sớm nhưng vẫn nhận review 1–2 sao, nơi rủi ro có thể liên hệ với cấu trúc đơn hàng, seller, sản phẩm, phí vận chuyển hoặc các dạng ma sát dịch vụ khác. Đồng thời, các nghiên cứu trước chưa kết hợp đầy đủ prediction-time integrity, temporal validation, calibration cho lớp thiểu số, review self-selection và đánh giá utility dưới ngân sách hữu hạn. Do đó, cần một mô hình product-item dễ giải thích, được hiệu chỉnh và tổng hợp có version lên order, chỉ sử dụng thông tin có sẵn trước review; tuy nhiên, do nhãn review chỉ có ở cấp order và thiếu dữ liệu can thiệp, mô hình không thể quy nguyên nhân cho item hoặc suy ra hiệu quả nhân quả của một biện pháp service recovery cụ thể.

## 4. Mục tiêu nghiên cứu đề xuất

Xây dựng và đánh giá một khung dự báo có hiệu chỉnh và dễ giải thích nhằm nhận diện review 1–2 sao trong nhóm đơn Olist đã được giao đúng hoặc sớm, sử dụng duy nhất thông tin có sẵn tại thời điểm xác nhận giao hàng và trước khi review; sau đó kiểm tra liệu risk score có cải thiện hiệu quả ưu tiên case dưới ngân sách chăm sóc hữu hạn so với các baseline đơn giản hay không.

## 5. Research Questions

### Câu hỏi nghiên cứu chính

**RQ:** Trong số các đơn hàng Olist đã được giao đúng hoặc sớm, một mô hình machine learning được hiệu chỉnh, chỉ sử dụng thông tin có sẵn tại thời điểm xác nhận giao hàng và trước khi review, có thể dự báo review 1–2 sao và ưu tiên các case rủi ro dưới ngân sách chăm sóc hữu hạn tốt hơn các baseline đơn giản đến mức nào?

### Các câu hỏi thành phần

**RQ1 — Predictability:** Mức độ chính xác của việc dự báo review 1–2 sao trong nhóm đơn giao đúng/sớm là bao nhiêu khi đánh giá theo thời gian bằng PR-AUC, recall lớp thiểu số và calibration?

**RQ2 — Drivers:** Sau khi loại bỏ trạng thái giao trễ, những nhóm đặc trưng nào đóng góp nhiều nhất vào rủi ro review thấp: thời gian giao tuyệt đối, phí vận chuyển, độ phức tạp đơn hàng, đặc trưng seller/sản phẩm, thanh toán hay địa lý?

**RQ3 — Model design:** Các mô hình boosting không resample hoặc cost-sensitive có tạo ra discrimination và calibration tốt hơn Logistic Regression, Random Forest và các biến thể SMOTE đã được hiệu chỉnh lại hay không?

**RQ4 — Decision utility:** Ở các mức ngân sách kiểm tra hoặc chăm sóc 5%, 10% và 20%, chiến lược risk-only hoặc risk × order value có phát hiện được nhiều đơn review thấp hoặc nhiều giá trị đơn review thấp hơn random và VALUE_ONLY hay không?

**RQ5 — Review selection:** Việc mô hình hóa riêng xác suất có review và xác suất review 1–2 sao khi có review làm thay đổi kết luận về các yếu tố rủi ro và khả năng ưu tiên case như thế nào?

## 6. Phạm vi và thiết kế tối thiểu để trả lời RQ

- **Đơn vị ML:** product item thuộc đơn đã giao trước hoặc đúng `order_estimated_delivery_date`; đơn hàng là đơn vị temporal split, bootstrap và workflow. Item kế thừa nhãn review cấp đơn và không được diễn giải là nguyên nhân của review.
- **Prediction time:** ngay sau `order_delivered_customer_date`, trước `review_creation_date`.
- **Outcome chính:** review score 1–2 trong số đơn có review.
- **Outcome phụ:** có review hay không; dùng để mô tả hoặc mô hình hóa selection process.
- **Feature hợp lệ:** thông tin order, item, seller, product, payment, customer geography, freight, số item/seller, delivery duration và earliness/slack có tại prediction time.
- **Feature loại trừ:** review text, review timestamp, trường phát sinh sau review và mọi biến dùng thông tin tương lai so với prediction time.
- **Validation:** rolling-origin hoặc train/test split theo thời gian; không dùng random split làm kết quả chính.
- **Baseline dự báo:** prevalence, Logistic Regression, Random Forest và một boosting model như CatBoost/LightGBM/XGBoost.
- **Baseline quyết định:** random, VALUE_ONLY, risk-only và risk × value.
- **Metric:** PR-AUC, ROC-AUC phụ trợ, recall/precision/F1 lớp 1–2 sao, Brier score, calibration curve, recall@budget hoặc value captured@budget, kèm bootstrap confidence interval.
- **Giải thích:** SHAP ở mức toàn cục và case-level; không diễn giải SHAP như quan hệ nhân quả.

## 7. Giả thuyết có thể kiểm định

- **H1:** Ngay cả trong nhóm giao đúng/sớm, thời gian giao tuyệt đối dài hơn làm tăng xác suất review 1–2 sao.
- **H2:** Độ phức tạp đơn hàng cao hơn, thể hiện qua nhiều item hoặc nhiều seller, làm tăng rủi ro review thấp.
- **H3:** Boosting cost-sensitive hoặc threshold tuning cho calibration tốt hơn mô hình dùng SMOTE chưa hiệu chỉnh lại.
- **H4:** Risk × value vượt VALUE_ONLY về giá trị đơn review thấp được phát hiện tại ít nhất một mức ngân sách, nhưng lợi thế không được giả định trước và phải có khoảng tin cậy.
- **H5:** Các yếu tố dự báo việc khách viết review không hoàn toàn trùng với các yếu tố dự báo review 1–2 sao khi review được quan sát.

## 8. Ranh giới diễn giải

- Không đồng nhất “không có review thấp” với “khách hài lòng”.
- Không đồng nhất review thấp với churn hoặc không mua lại.
- Không gọi giá trị đơn được phát hiện là giá trị “cứu vãn được” nếu chưa có treatment outcome.
- Không khuyến nghị tự động voucher, refund hoặc liên hệ khách chỉ từ risk score.
- Không xem feature importance hoặc SHAP là bằng chứng nhân quả.
- Không tuyên bố khả năng khái quát ngoài Olist nếu chưa có external validation.

## 9. Vấn đề chất lượng tài liệu cần xử lý trước khi nộp

- Hàng “When Faster Online Delivery Backfires” đang gắn DOI `10.1093/jamia/ocac093`, trùng với bài JAMIA về class imbalance; cần kiểm tra và sửa DOI.
- Hàng “e-LSQ” đang gắn arXiv `2201.08528`, trùng với “To SMOTE, or not to SMOTE?”; cần thay bằng nguồn đúng.
- “Retention Futility” xuất hiện hai lần, trong đó một hàng thiếu title/author; nên gộp thành một citation chuẩn.
- Các con số nội bộ như “67,5% đơn bị chê được giao đúng hạn” và tỷ lệ theo số ngày giao cần được tái lập bằng notebook hoặc truy vấn dữ liệu trước khi đưa vào luận văn.
- Các preprint năm 2026 và journal metadata cần được kiểm tra lại trạng thái xuất bản, phiên bản và bibliographic details.

## Connections

- Bài toán nối **customer satisfaction prediction** với **budgeted order prioritization**, nhưng không vượt sang **uplift modeling** khi chưa có dữ liệu can thiệp.
- Review self-selection nối bài toán nhãn với selection bias: mô hình dự báo outcome quan sát, không trực tiếp đo trạng thái tâm lý của toàn bộ khách hàng.
- Calibration nối chất lượng mô hình với quyết định: xác suất sai hiệu chỉnh có thể làm sai thứ tự hoặc utility của policy dù AUC không đổi.
- Temporal validation nối phương pháp nghiên cứu với triển khai: mọi feature và label phải được kiểm tra theo prediction time.

## Open Questions

- Olist có đủ dấu thời gian để bảo đảm một cửa sổ can thiệp thực tế giữa xác nhận giao hàng và review hay không?
- Có thể xác định split delivery trực tiếp từ dữ liệu hay chỉ dùng số seller/item làm proxy?
- `customer_unique_id` có đủ lịch sử để xây seller/customer history không leakage, khi đa số khách chỉ mua một lần?
- Utility nên dùng order value, margin proxy hay chỉ số case captured khi Olist không có chi phí can thiệp và outcome treatment?
- Kết quả có ổn định theo category, seller tenure và các giai đoạn thời gian khác nhau không?

## Sources

- `School/ML/Lược khảo.md`
