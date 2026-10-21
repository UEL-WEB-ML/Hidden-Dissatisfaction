# Problem Statement: Nhận diện bất mãn ẩn ở cấp sản phẩm trong các đơn hàng Olist giao đúng hạn

## 1. Bối cảnh vấn đề

Sự hài lòng của khách hàng là một chỉ báo quan trọng đối với chất lượng dịch vụ thương mại điện tử. Trong nhiều nghiên cứu, giao hàng trễ được xem là một nguyên nhân chính dẫn đến đánh giá tiêu cực. Vì vậy, các quy trình quản lý rủi ro thường ưu tiên những đơn bị trễ so với ngày giao dự kiến.

Tuy nhiên, giao hàng đúng hạn không bảo đảm rằng khách hàng hài lòng. Một số đơn được giao đúng hoặc sớm hơn ngày dự kiến vẫn nhận đánh giá 1 hoặc 2 sao. Các đánh giá này có thể liên quan đến thời gian giao thực tế, phí vận chuyển, chất lượng sản phẩm, đặc điểm của người bán, cấu trúc đơn hàng, số lượng sản phẩm, số lượng người bán hoặc những vấn đề khác trong quá trình phục vụ.

Nhóm đơn hàng này tạo thành một điểm mù trong cách quản lý chỉ dựa vào tình trạng giao trễ. Nếu doanh nghiệp chỉ kiểm tra các đơn giao trễ, nhiều trường hợp có nguy cơ nhận đánh giá thấp sẽ không được nhận diện. Trong tài liệu này, hiện tượng đó được gọi là bất mãn ẩn, nghĩa là đánh giá tiêu cực xuất hiện dù đơn hàng không vi phạm ngày giao dự kiến.

## 2. Tổng quan về khoảng trống nghiên cứu

Khoảng trống thứ nhất nằm ở đối tượng nghiên cứu. Nhiều công trình tập trung vào toàn bộ đơn hàng hoặc nhóm giao trễ, trong khi nhóm giao đúng hạn nhưng vẫn nhận đánh giá thấp chưa được xem như một đối tượng dự báo riêng.

Khoảng trống thứ hai nằm ở thời điểm dự báo. Một số nghiên cứu sử dụng cách chia dữ liệu ngẫu nhiên hoặc sử dụng thông tin chỉ xuất hiện sau khi khách hàng đã đánh giá. Cách thiết kế này có thể tạo ra kết quả tốt trong thử nghiệm nhưng không phản ánh đúng điều kiện sử dụng thực tế. Một mô hình có khả năng triển khai cần chỉ sử dụng thông tin đã có tại thời điểm đơn hàng được xác nhận là đã giao và trước khi đánh giá được tạo.

Khoảng trống thứ ba liên quan đến đánh giá lớp thiểu số. Đánh giá 1 hoặc 2 sao chiếm tỷ lệ nhỏ hơn so với các mức đánh giá còn lại. Vì vậy, độ chính xác tổng thể có thể cao ngay cả khi mô hình bỏ sót phần lớn trường hợp cần quan tâm. Việc đánh giá cần tập trung vào khả năng phát hiện đánh giá thấp và mức độ đáng tin cậy của xác suất dự báo.

Khoảng trống thứ tư liên quan đến hành vi viết đánh giá. Không phải khách hàng nào cũng để lại đánh giá. Do đó, dữ liệu quan sát chỉ phản ánh mức điểm của những đơn có đánh giá và không đại diện đầy đủ cho trạng thái hài lòng của tất cả khách hàng.

Khoảng trống thứ năm nằm giữa chất lượng dự báo và giá trị sử dụng. Một mô hình có chỉ số thống kê tốt chưa chắc giúp lựa chọn trường hợp hiệu quả hơn các quy tắc đơn giản. Nghiên cứu cần kiểm tra liệu mô hình có tìm được nhiều đơn đánh giá thấp hơn khi số lượng trường hợp có thể kiểm tra bị giới hạn hay không.

Khoảng trống cuối cùng liên quan đến tác động của biện pháp chăm sóc. Dữ liệu Olist không ghi nhận đầy đủ việc khách hàng nhận biện pháp hỗ trợ nào và phản ứng của họ sau biện pháp đó. Vì vậy, dữ liệu có thể hỗ trợ nhận diện rủi ro nhưng không thể chứng minh rằng một hành động như hoàn tiền, tặng ưu đãi hoặc liên hệ khách hàng sẽ làm thay đổi kết quả.

## 3. Phát biểu vấn đề nghiên cứu

Đồ án giải quyết bài toán nhận diện product item trong các đơn hàng Olist đã được giao đúng hoặc sớm hơn ngày dự kiến nhưng đơn vẫn có nguy cơ nhận đánh giá 1 hoặc 2 sao. Mô hình hoạt động ở cấp product item, chỉ sử dụng thông tin có sẵn tại thời điểm xác nhận giao hàng và trước khi khách hàng gửi đánh giá. Các điểm item được tổng hợp thành điểm cấp đơn bằng quy tắc có version; phiên bản đầu tiên là `max-v1`, tức điểm đơn bằng điểm item cao nhất.

Olist chỉ cung cấp review ở cấp đơn hàng. Vì vậy, mỗi item kế thừa nhãn review của đơn chứa nó. Điểm item phải được hiểu là rủi ro review thấp của đơn trong bối cảnh item đó, không phải nhãn bất mãn riêng của sản phẩm và không phải bằng chứng sản phẩm gây ra đánh giá thấp.

Vấn đề nghiên cứu không chỉ là xây dựng một mô hình có khả năng phân loại. Trọng tâm là xây dựng một quy trình dự báo phù hợp với thời gian thực tế, nhận diện được lớp đánh giá thấp, cung cấp xác suất đủ tin cậy, giải thích được các yếu tố liên quan và hỗ trợ xếp thứ tự ưu tiên khi nguồn lực kiểm tra có giới hạn.

Kết quả của đồ án được hiểu là công cụ hỗ trợ phát hiện và ưu tiên trường hợp có rủi ro. Kết quả không được hiểu là bằng chứng về nguyên nhân của sự bất mãn hoặc hiệu quả của một biện pháp chăm sóc cụ thể.

## 4. Câu hỏi nghiên cứu

### 4.1. Câu hỏi nghiên cứu chính

Trong nhóm product item thuộc các đơn hàng Olist được giao đúng hoặc sớm hơn ngày dự kiến, mô hình học máy chỉ sử dụng thông tin có sẵn trước khi khách hàng viết đánh giá có thể ước lượng rủi ro review 1 hoặc 2 sao của đơn và tạo danh sách ưu tiên cấp đơn tốt hơn các phương pháp đơn giản ở mức độ nào?

### 4.2. Câu hỏi nghiên cứu thành phần

1. Mô hình có thể phát hiện đánh giá 1 hoặc 2 sao với chất lượng như thế nào khi dữ liệu huấn luyện và kiểm tra được chia theo thời gian?

2. Xác suất do mô hình tạo ra có phản ánh gần đúng tỷ lệ đánh giá thấp thực tế hay không?

3. Những nhóm thông tin nào có liên hệ mạnh nhất với rủi ro đánh giá thấp sau khi đã loại trừ các đơn giao trễ?

4. Mô hình tăng cường có xét đến mất cân bằng lớp có hiệu quả hơn hồi quy logistic, rừng ngẫu nhiên và các phương pháp cân bằng lại dữ liệu hay không?

5. Khi chỉ có thể kiểm tra một tỷ lệ giới hạn các đơn hàng, cách xếp thứ tự theo rủi ro hoặc theo kết hợp giữa rủi ro và giá trị đơn hàng có hiệu quả hơn lựa chọn ngẫu nhiên và lựa chọn theo giá trị đơn hàng hay không?

6. Việc tách riêng khả năng khách hàng viết đánh giá và khả năng họ để lại đánh giá thấp có làm thay đổi kết luận về các yếu tố rủi ro hay không?

## 5. Mục tiêu nghiên cứu

### 5.1. Mục tiêu tổng quát

Mục tiêu của đồ án là xây dựng và đánh giá một quy trình học máy có khả năng nhận diện bất mãn ẩn trong các đơn hàng Olist được giao đúng hạn, đồng thời kiểm tra giá trị của mô hình đối với việc ưu tiên trường hợp trong điều kiện nguồn lực giới hạn.

### 5.2. Mục tiêu cụ thể

1. Xây dựng tập dữ liệu ở cấp product item với mốc thời gian dự báo được xác định rõ ràng, đồng thời giữ mọi item của cùng một order trong một temporal split.

2. Ngăn ngừa việc sử dụng thông tin phát sinh sau thời điểm dự báo.

3. So sánh các mô hình cơ sở với ít nhất một mô hình tăng cường phù hợp cho dữ liệu dạng bảng.

4. Đánh giá khả năng phát hiện lớp đánh giá thấp thay vì chỉ dựa vào độ chính xác tổng thể.

5. Đánh giá và điều chỉnh độ tin cậy của xác suất dự báo khi cần thiết.

6. Xác định các nhóm thông tin có liên hệ với nguy cơ đánh giá thấp bằng phương pháp giải thích mô hình.

7. Đánh giá hiệu quả xếp thứ tự ưu tiên tại nhiều mức ngân sách kiểm tra.

8. Làm rõ giới hạn do việc khách hàng tự lựa chọn có viết đánh giá hay không.

## 6. Đối tượng và kết quả mục tiêu

Đối tượng nghiên cứu là các product item thuộc đơn hàng Olist đã được giao cho khách hàng không muộn hơn ngày giao dự kiến. Đơn vị ML là một product item; đơn vị workflow, chia tập và bootstrap là một order.

Biến kết quả chính là việc đơn hàng chứa item nhận đánh giá 1 hoặc 2 sao trong nhóm đơn có đánh giá. Mọi item của cùng một đơn kế thừa cùng nhãn. Nhóm này được xem là nhóm cần phát hiện; các mức điểm còn lại được dùng làm nhóm so sánh.

Kết quả đầu ra của mô hình là điểm rủi ro cho từng product item. Hệ thống tổng hợp các điểm item bằng `max-v1` để tạo điểm order và sắp xếp order trong Risk Queue. Một kết quả phụ có thể được xây dựng để ước lượng khả năng một đơn hàng có đánh giá, qua đó hỗ trợ phân tích giới hạn của dữ liệu.

Người sử dụng dự kiến của kết quả là nhóm phân tích dữ liệu hoặc nhóm vận hành dịch vụ khách hàng. Mô hình cung cấp danh sách ưu tiên để con người xem xét và không tự động quyết định biện pháp áp dụng cho khách hàng.

## 7. Tiêu chí thành công

### 7.1. Tính đúng đắn của thiết kế

Nghiên cứu được xem là đúng về thiết kế khi toàn bộ thông tin đầu vào đã tồn tại tại thời điểm xác nhận giao hàng, không sử dụng nội dung đánh giá, thời gian tạo đánh giá hoặc bất kỳ thông tin nào phát sinh sau thời điểm dự báo. Việc chia dữ liệu chính phải theo thứ tự thời gian ở cấp order; không được để item của cùng một order xuất hiện ở nhiều tập.

### 7.2. Khả năng phân biệt rủi ro

Chỉ số chính là PR AUC ở cấp item và sau tổng hợp `max-v1` ở cấp order. Khoảng tin cậy phải bootstrap theo order để không coi các item cùng đơn là quan sát độc lập. Mô hình đề xuất cần tốt hơn mô hình chỉ dự báo theo tỷ lệ đánh giá thấp trong dữ liệu và tốt hơn hồi quy logistic trên tập kiểm tra theo thời gian.

Recall của nhóm đánh giá thấp phải được báo cáo để thể hiện tỷ lệ trường hợp thực sự có đánh giá 1 hoặc 2 sao được phát hiện. Precision phải được báo cáo cùng recall để cho biết tỷ lệ cảnh báo đúng trong số các trường hợp được mô hình cảnh báo. ROC AUC và F1 được sử dụng như chỉ số bổ sung, không phải căn cứ duy nhất để chọn mô hình.

### 7.3. Độ tin cậy của xác suất

Độ tin cậy của xác suất được đánh giá bằng chỉ số Brier và biểu đồ so sánh xác suất dự báo với tỷ lệ thực tế. Chỉ số Brier thấp hơn thể hiện sai số xác suất nhỏ hơn. Mô hình thành công khi xác suất sau hiệu chỉnh tốt hơn hoặc ít nhất không kém mô hình trước hiệu chỉnh trên dữ liệu kiểm tra theo thời gian.

### 7.4. Hiệu quả ưu tiên

Tại các mức ngân sách kiểm tra tương ứng với 5 phần trăm, 10 phần trăm và 20 phần trăm số đơn, nghiên cứu đo tỷ lệ đơn đánh giá thấp được tìm thấy và tổng giá trị của các đơn đánh giá thấp được tìm thấy.

Chiến lược dựa trên rủi ro được xem là có giá trị sử dụng khi tốt hơn lựa chọn ngẫu nhiên và ít nhất cạnh tranh được với cách chỉ ưu tiên đơn có giá trị cao. Kết quả cần được trình bày kèm khoảng tin cậy để tránh kết luận từ khác biệt ngẫu nhiên.

### 7.5. Khả năng giải thích và độ ổn định

Mô hình cần cung cấp được giải thích ở mức toàn bộ dữ liệu và ở mức từng trường hợp. Các yếu tố quan trọng phải có ý nghĩa hợp lý trong bối cảnh đơn hàng. Kết quả cũng cần được kiểm tra theo thời gian và theo một số nhóm chính như loại sản phẩm hoặc đặc điểm người bán để xác định mức độ ổn định.

### 7.6. Điều kiện kết luận thành công tổng thể

Đồ án được xem là đạt mục tiêu khi đáp ứng đồng thời bốn điều kiện. Thứ nhất, thiết kế không sử dụng thông tin tương lai. Thứ hai, mô hình cải thiện khả năng nhận diện đánh giá thấp so với các mô hình cơ sở. Thứ ba, xác suất dự báo đạt độ tin cậy phù hợp sau bước kiểm tra hoặc hiệu chỉnh. Thứ tư, cách ưu tiên dựa trên mô hình tạo ra lợi ích rõ ràng so với lựa chọn ngẫu nhiên tại ít nhất một mức ngân sách đã xác định.

Nếu mô hình không vượt phương pháp chỉ chọn theo giá trị đơn hàng, kết quả vẫn có giá trị nghiên cứu nếu quy trình đánh giá được thực hiện đúng và giới hạn này được báo cáo rõ ràng. Thành công của nghiên cứu không phụ thuộc vào việc phải chứng minh mọi giả thuyết ban đầu.

## 8. Phạm vi nghiên cứu

### 8.1. Phạm vi dữ liệu

Nghiên cứu sử dụng bộ dữ liệu thương mại điện tử Olist. Phân tích chính chỉ bao gồm product item thuộc các đơn đã giao và có ngày giao thực tế không muộn hơn ngày giao dự kiến. Việc học nhãn review chỉ được thực hiện trên các đơn có đánh giá quan sát được.

### 8.2. Phạm vi thông tin đầu vào

Thông tin đầu vào có thể bao gồm đặc điểm đơn hàng, sản phẩm, người bán, thanh toán, vị trí địa lý, phí vận chuyển, số lượng sản phẩm, số lượng người bán, thời gian giao thực tế và khoảng thời gian giao sớm so với dự kiến. Mọi thông tin phải được kiểm tra theo thời điểm xuất hiện trong quy trình.

### 8.3. Phạm vi phương pháp

Nghiên cứu so sánh mô hình theo tỷ lệ cơ bản, hồi quy logistic, rừng ngẫu nhiên và ít nhất một mô hình tăng cường. Các cách xử lý mất cân bằng lớp được đánh giá thông qua trọng số lớp, điều chỉnh ngưỡng và thử nghiệm cân bằng lại dữ liệu. Nếu dữ liệu được cân bằng lại, xác suất phải được kiểm tra và hiệu chỉnh lại.

### 8.4. Phạm vi đánh giá

Đánh giá chính sử dụng cách chia dữ liệu theo thời gian. Kết quả bao gồm chất lượng phân loại, độ tin cậy của xác suất, khả năng giải thích và hiệu quả ưu tiên trong ngân sách hữu hạn. Các kết quả từ cách chia ngẫu nhiên, nếu có, chỉ mang tính tham khảo.

### 8.5. Phạm vi suy luận

Kết luận chỉ áp dụng trực tiếp cho dữ liệu Olist và giai đoạn được quan sát. Khái niệm bất mãn trong nghiên cứu được đo bằng đánh giá 1 hoặc 2 sao của những khách hàng đã viết đánh giá. Nghiên cứu không khẳng định đã đo được trạng thái hài lòng của toàn bộ khách hàng.

## 9. Kết quả bàn giao dự kiến

Kết quả của đồ án gồm một tập dữ liệu đã được xây dựng theo đúng mốc thời gian, một quy trình huấn luyện và đánh giá có thể lặp lại, bảng so sánh các mô hình, đánh giá độ tin cậy của xác suất, phân tích các yếu tố liên quan, và kết quả thử nghiệm ưu tiên trường hợp theo ngân sách.

Sản phẩm cuối cùng cần cho phép trả lời rõ ba vấn đề. Vấn đề thứ nhất là liệu bất mãn ẩn có thể được dự báo ở mức hữu ích hay không. Vấn đề thứ hai là những thông tin nào có liên hệ đáng kể với rủi ro này. Vấn đề thứ ba là mô hình có hỗ trợ phân bổ nguồn lực kiểm tra tốt hơn các quy tắc đơn giản hay không.

## 10. Tài liệu nền

Nội dung phát biểu vấn đề này được tổng hợp từ báo cáo lược khảo về bất mãn ẩn trên Olist trong thư mục `docs` và cần được cập nhật nếu phạm vi dữ liệu hoặc thiết kế thực nghiệm của đồ án thay đổi.
