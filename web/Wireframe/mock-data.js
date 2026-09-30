// =========================================================
// mock-data.js
// DỮ LIỆU GIẢ theo contract ML → Web, dùng cho wireframe.
// Khi có kết quả thật từ nhóm ML thì thay mảng này bằng dữ liệu từ backend.
//
// Contract: order_id · risk_score · risk_level · top_reasons · recommended_action
// Các field còn lại (khách, seller, ngày...) lấy từ 9 bảng Olist.
// =========================================================

var orders = [
  {
    order_id: "a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30",
    risk_score: 0.91, risk_level: "High",
    top_reasons: ["Seller mất 5 ngày mới bàn giao cho đơn vị vận chuyển", "Danh mục có tỉ lệ bị chê cao (office_furniture)", "Giá trị đơn cao hơn 80% đơn khác"],
    recommended_action: "Contact Customer",
    customer_city: "Rio de Janeiro", customer_state: "RJ",
    seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "office_furniture",
    order_value: 459.90, freight: 42.30,
    purchase_date: "2018-03-02", approved_date: "2018-03-02", carrier_date: "2018-03-07",
    delivered_date: "2018-03-20", estimated_date: "2018-04-05",
    status: "Chưa xử lý"
  },
  {
    order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47",
    risk_score: 0.84, risk_level: "High",
    top_reasons: ["Seller mất 4 ngày mới bàn giao cho vận chuyển", "Khoảng cách seller – khách trên 2.000 km", "Phí ship cao hơn 70% đơn khác"],
    recommended_action: "Contact Customer",
    customer_city: "Fortaleza", customer_state: "CE",
    seller_id: "4a3ca9315b744ce9f8e9374361493884", category: "bed_bath_table",
    order_value: 189.00, freight: 38.75,
    purchase_date: "2018-05-11", approved_date: "2018-05-11", carrier_date: "2018-05-15",
    delivered_date: "2018-05-29", estimated_date: "2018-06-12",
    status: "Đang xử lý"
  },
  {
    order_id: "c0d8e4f1a29b4b7c8d6e5f3a2b1c0d9e",
    risk_score: 0.78, risk_level: "High",
    top_reasons: ["Seller có 18% đơn cũ bị đánh giá ≤ 2 sao", "Seller mất 3 ngày mới bàn giao cho vận chuyển"],
    recommended_action: "Contact Customer",
    customer_city: "São Paulo", customer_state: "SP",
    seller_id: "1f50f920176fa81dab994f9023523100", category: "watches_gifts",
    order_value: 229.99, freight: 16.10,
    purchase_date: "2017-11-24", approved_date: "2017-11-24", carrier_date: "2017-11-27",
    delivered_date: "2017-12-04", estimated_date: "2017-12-15",
    status: "Chưa xử lý"
  },
  {
    order_id: "9b7a6c5d4e3f4a2b9c8d7e6f5a4b3c21",
    risk_score: 0.66, risk_level: "Medium",
    top_reasons: ["Seller mất 2 ngày mới bàn giao cho vận chuyển", "Danh mục có tỉ lệ bị chê cao (computers_accessories)"],
    recommended_action: "Monitor",
    customer_city: "Belo Horizonte", customer_state: "MG",
    seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories",
    order_value: 139.90, freight: 19.80,
    purchase_date: "2018-01-15", approved_date: "2018-01-15", carrier_date: "2018-01-17",
    delivered_date: "2018-01-26", estimated_date: "2018-02-09",
    status: "Chưa xử lý"
  },
  {
    order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a",
    risk_score: 0.58, risk_level: "Medium",
    top_reasons: ["Đơn có nhiều món từ 2 seller khác nhau", "Phí ship cao hơn 60% đơn khác"],
    recommended_action: "Monitor",
    customer_city: "Curitiba", customer_state: "PR",
    seller_id: "955fee9216a65b617aa5c0531780ce60", category: "housewares",
    order_value: 97.50, freight: 24.40,
    purchase_date: "2018-04-03", approved_date: "2018-04-03", carrier_date: "2018-04-05",
    delivered_date: "2018-04-12", estimated_date: "2018-04-27",
    status: "Đã xong"
  },
  {
    order_id: "e8f7a6b5c4d34e2f1a0b9c8d7e6f5a43",
    risk_score: 0.52, risk_level: "Medium",
    top_reasons: ["Seller mới, dưới 10 đơn trước đó"],
    recommended_action: "Monitor",
    customer_city: "Salvador", customer_state: "BA",
    seller_id: "6560211a19b47992c3666cc44a7e94c0", category: "sports_leisure",
    order_value: 74.90, freight: 21.15,
    purchase_date: "2017-09-19", approved_date: "2017-09-19", carrier_date: "2017-09-21",
    delivered_date: "2017-10-02", estimated_date: "2017-10-16",
    status: "Chưa xử lý"
  },
  {
    order_id: "3a4b5c6d7e8f4a9b0c1d2e3f4a5b6c78",
    risk_score: 0.31, risk_level: "Low",
    top_reasons: ["Không có yếu tố rủi ro nổi bật"],
    recommended_action: "No Action",
    customer_city: "Campinas", customer_state: "SP",
    seller_id: "cc419e0650a3c5ba77189a1882b7556a", category: "health_beauty",
    order_value: 59.90, freight: 8.72,
    purchase_date: "2018-02-08", approved_date: "2018-02-08", carrier_date: "2018-02-09",
    delivered_date: "2018-02-13", estimated_date: "2018-02-28",
    status: "Chưa xử lý"
  },
  {
    order_id: "f0e1d2c3b4a54f6e7d8c9b0a1f2e3d4c",
    risk_score: 0.18, risk_level: "Low",
    top_reasons: ["Không có yếu tố rủi ro nổi bật"],
    recommended_action: "No Action",
    customer_city: "Porto Alegre", customer_state: "RS",
    seller_id: "8b321bb669392f5163d04c59e235e066", category: "toys",
    order_value: 45.00, freight: 15.23,
    purchase_date: "2017-07-21", approved_date: "2017-07-21", carrier_date: "2017-07-24",
    delivered_date: "2017-08-01", estimated_date: "2017-08-18",
    status: "Chưa xử lý"
  }
];

// Nhân viên xử lý (bảng users)
var users = ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"];

// Lịch sử hành động (bảng actions)
var actions = [
  { order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", action_type: "Contact Customer", user: "Trần Thị B",
    status: "Đang xử lý", note: "Đã gọi, khách chưa nghe máy", created_at: "2018-05-30 09:15" },
  { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", action_type: "Monitor", user: "Nguyễn Văn A",
    status: "Đã xong", note: "Khách đã đánh giá 4 sao", created_at: "2018-04-14 14:02" }
];
