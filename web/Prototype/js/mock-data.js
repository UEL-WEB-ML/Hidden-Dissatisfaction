// =========================================================
// mock-data.js
// DỮ LIỆU GIẢ cho backend giả (mock-server.js), bám theo logical data object của FRD v2.0 mục 4.1:
//   Order Risk Case · Product Item Risk Output · Order Risk Aggregation · Review Cycle
//   Review Assignment · Review Status · Review Activity · Review Outcome · Audit Event
//   User/Role · Parameter Configuration
// Thêm theo feedback giao diện 13/10 (chưa có trong FRD, chờ BA bổ sung): Case Comment, Manager Decision, Contact Evidence.
// Frontend KHÔNG đọc file này trực tiếp; mọi dữ liệu đi qua js/api.js theo API_CONTRACT_olist_hidden_dissatisfaction.md.
// Khi có backend thật thì bỏ file này cùng mock-server.js.
// =========================================================

var MOCK_DB = (function () {

  // Thời điểm "hiện tại" giả lập (thứ Hai 04/06/2018) để tính SLA, aging cho ổn định khi xem prototype
  var now = "2018-06-04 14:00";

  // ---------- Ngưỡng HIGH/MEDIUM: thuộc model (threshold version), Manager KHÔNG sửa được (BRD 6.1) ----------
  var threshold = { threshold_version: "thr-v1", high_from: 0.70, medium_from: 0.45 };

  // ---------- Parameter Configuration (BRD 6.9, FRD F10) ----------
  // Mỗi dòng là một phiên bản của một tham số. Giá trị đang hiệu lực = phiên bản mới nhất có effective_at <= giờ hiện tại.
  // Phiên bản có effective_at ở tương lai là "đã lên lịch". Không sửa/xoá dòng cũ, chỉ thêm dòng mới.
  // brd: true = BRD 6.9/F10-S02 có nêu; false = đề xuất bổ sung (BRD 6.7 có quy tắc nhưng F10-S02 chưa liệt kê).
  var PARAM_DEFS = [
    { key: "sla_calendar",        unit: "enum",  brd: true,  value: "CALENDAR" },        // CALENDAR = giờ đồng hồ, BUSINESS_HOURS = giờ làm việc
    { key: "sla_hours_high",      unit: "hours", brd: true,  value: 4 },
    { key: "sla_hours_medium",    unit: "hours", brd: true,  value: 24 },
    { key: "sla_hours_low",       unit: "hours", brd: true,  value: 48 },
    { key: "first_touch_hours",   unit: "hours", brd: false, value: 2 },
    { key: "capacity",            unit: "orders", brd: true, value: 5 },
    { key: "capacity_warn",       unit: "orders", brd: false, value: 4 },
    { key: "max_contact",         unit: "times", brd: true,  value: 3 },
    { key: "retry_gap_days",      unit: "days",  brd: true,  value: 1 },
    { key: "soon_hours",          unit: "hours", brd: false, value: 2 },
    { key: "stale_hours",         unit: "hours", brd: false, value: 24 },
    { key: "aging_days",          unit: "days",  brd: false, value: 2 },
    { key: "reopen_review_days",  unit: "days",  brd: false, value: 7 },
    { key: "reopen_review_times", unit: "times", brd: false, value: 2 }
  ];
  var params = [];
  for (var p = 0; p < PARAM_DEFS.length; p++) {
    params.push({ key: PARAM_DEFS[p].key, value: PARAM_DEFS[p].value, version: 1, effective_at: "2018-05-01 00:00",
      actor: "u4", created_at: "2018-04-30 17:00", reason: "Initial configuration approved by Product Owner" });
  }
  // Lịch sử thay đổi: tăng SLA của MEDIUM (đã hiệu lực) và tăng capacity (lên lịch, chưa hiệu lực)
  params.push({ key: "sla_hours_medium", value: 24, version: 2, effective_at: "2018-05-21 08:00", actor: "u4",
    created_at: "2018-05-18 16:30", reason: "Keep 24 h after the trial week; explicit version for the audit" });
  params.push({ key: "capacity", value: 6, version: 2, effective_at: "2018-06-08 08:00", actor: "u4",
    created_at: "2018-06-04 09:50", reason: "Afternoon shift added from 8 June" });

  // ---------- User/Role ----------
  // preferred_language: ngôn ngữ giao diện lưu theo user (FRD F11-S01)
  var users = [
    { id: "u1", full_name: "Nguyễn Văn A", role: "SPECIALIST", username: "nhanvien3", preferred_language: "vi", created_at: "2018-04-20 09:00" },
    { id: "u2", full_name: "Trần Thị B",   role: "SPECIALIST", username: "nhanvien",  preferred_language: null, created_at: "2018-04-20 09:00" },
    { id: "u3", full_name: "Lê Văn C",     role: "SPECIALIST", username: "nhanvien2", preferred_language: null, created_at: "2018-04-22 09:00" },
    { id: "u4", full_name: "Phạm Văn D",   role: "MANAGER",    username: "quanly",    preferred_language: null, created_at: "2018-04-18 09:00" }
  ];

  // Tài khoản mẫu: tạo sẵn, không có đăng ký.
  // Bản thật: mật khẩu được mã hoá và kiểm tra ở máy chủ, không để trong file JS như thế này.
  var accounts = [
    { username: "nhanvien",  password: "123456", user_id: "u2" },   // Specialist đang giữ 3/5
    { username: "nhanvien2", password: "123456", user_id: "u3" },   // Specialist đã đủ 5/5
    { username: "nhanvien3", password: "123456", user_id: "u1" },   // Specialist đã lưu ngôn ngữ tiếng Việt
    { username: "quanly",    password: "123456", user_id: "u4" }    // Manager
  ];

  // ---------- Order Risk Case + Status + Assignment + Outcome ----------
  // risk_score, risk_level, top_factors, suggested_action, model_version, predicted_at: output gốc của model, KHÔNG ai sửa.
  // queued_at: lúc case vào Risk Queue (dùng tính aging và SLA).
  // Chỉ có field biết được trước mốc dự báo (sau khi giao, trước khi khách viết review).
  var cases = [
    { order_id: "a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30", risk_score: 0.91, risk_level: "HIGH",
      top_factors: ["Seller took 5 days to hand over to the carrier", "Category Office furniture has a high low-rating rate", "Order value higher than 80% of orders"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "office_furniture", customer_city: "Rio de Janeiro", customer_state: "RJ",
      order_value: 459.90, freight: 42.30,
      purchase_at: "2018-05-14", approved_at: "2018-05-14", carrier_at: "2018-05-19", delivered_at: "2018-06-01", estimated_at: "2018-06-12",
      queued_at: "2018-06-04 08:30", status: "PENDING", assignee: null, updated_at: "2018-06-04 08:30" },

    { order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", risk_score: 0.84, risk_level: "HIGH",
      top_factors: ["Seller took 4 days to hand over to the carrier", "Seller–customer distance over 2,000 km", "Shipping fee higher than 70% of orders"],
      seller_id: "4a3ca9315b744ce9f8e9374361493884", category: "bed_bath_table", customer_city: "Fortaleza", customer_state: "CE",
      order_value: 189.00, freight: 38.75,
      purchase_at: "2018-05-15", approved_at: "2018-05-15", carrier_at: "2018-05-19", delivered_at: "2018-06-02", estimated_at: "2018-06-14",
      queued_at: "2018-06-04 11:00", status: "IN_PROGRESS", assignee: "u2", updated_at: "2018-06-04 11:30" },

    { order_id: "c0d8e4f1a29b4b7c8d6e5f3a2b1c0d9e", risk_score: 0.78, risk_level: "HIGH",
      top_factors: ["18% of the seller's past orders were rated ≤ 2 stars", "Seller took 3 days to hand over to the carrier"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "watches_gifts", customer_city: "São Paulo", customer_state: "SP",
      order_value: 229.99, freight: 16.10,
      purchase_at: "2018-05-24", approved_at: "2018-05-24", carrier_at: "2018-05-27", delivered_at: "2018-06-03", estimated_at: "2018-06-11",
      queued_at: "2018-06-04 12:30", status: "PENDING", assignee: null, updated_at: "2018-06-04 12:30" },

    // Cùng score với đơn trên nhưng gần quá SLA hơn → đứng trước (tie-breaker BRD 6.2).
    { order_id: "7f3e2a1b0c9d4e8f7a6b5c4d3e2f1a0b", risk_score: 0.78, risk_level: "HIGH",
      top_factors: ["Order has items from 2 different sellers", "Category Computers & accessories has a high low-rating rate"],
      seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories", customer_city: "Belo Horizonte", customer_state: "MG",
      order_value: 312.40, freight: 27.90,
      purchase_at: "2018-05-22", approved_at: "2018-05-22", carrier_at: "2018-05-24", delivered_at: "2018-06-03", estimated_at: "2018-06-08",
      queued_at: "2018-06-04 10:45", status: "PENDING", assignee: null, updated_at: "2018-06-04 10:45" },

    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", risk_score: 0.81, risk_level: "HIGH",
      top_factors: ["Seller took 6 days to hand over to the carrier", "Category Furniture & decor has a high low-rating rate"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "furniture_decor", customer_city: "Recife", customer_state: "PE",
      order_value: 270.00, freight: 45.10,
      purchase_at: "2018-05-08", approved_at: "2018-05-08", carrier_at: "2018-05-14", delivered_at: "2018-05-31", estimated_at: "2018-06-06",
      queued_at: "2018-06-01 09:00", status: "IN_PROGRESS", assignee: "u3", updated_at: "2018-06-03 10:00" },

    { order_id: "8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f", risk_score: 0.74, risk_level: "HIGH",
      top_factors: ["Shipping fee higher than 85% of orders", "Seller–customer distance over 2,500 km"],
      seller_id: "4a3ca9315b744ce9f8e9374361493884", category: "bed_bath_table", customer_city: "Manaus", customer_state: "AM",
      order_value: 149.90, freight: 52.60,
      purchase_at: "2018-05-10", approved_at: "2018-05-10", carrier_at: "2018-05-12", delivered_at: "2018-06-02", estimated_at: "2018-06-15",
      queued_at: "2018-06-04 07:00", status: "IN_PROGRESS", assignee: "u3", updated_at: "2018-06-04 09:20" },

    { order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", risk_score: 0.72, risk_level: "HIGH",
      top_factors: ["Seller took 3 days to hand over to the carrier", "Order value higher than 75% of orders"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "office_furniture", customer_city: "Brasília", customer_state: "DF",
      order_value: 389.00, freight: 31.20,
      purchase_at: "2018-05-18", approved_at: "2018-05-18", carrier_at: "2018-05-21", delivered_at: "2018-06-01", estimated_at: "2018-06-07",
      queued_at: "2018-06-04 09:30", status: "IN_PROGRESS", assignee: "u3", updated_at: "2018-06-04 10:00" },

    { order_id: "4c5d6e7f8a9b4c0d1e2f3a4b5c6d7e8f", risk_score: 0.69, risk_level: "MEDIUM",
      top_factors: ["Seller took 3 days to hand over to the carrier", "Shipping fee higher than 60% of orders"],
      seller_id: "4a3ca9315b744ce9f8e9374361493884", category: "bed_bath_table", customer_city: "Goiânia", customer_state: "GO",
      order_value: 119.00, freight: 24.80,
      purchase_at: "2018-05-12", approved_at: "2018-05-12", carrier_at: "2018-05-15", delivered_at: "2018-05-31", estimated_at: "2018-06-05",
      queued_at: "2018-06-02 10:00", status: "IN_PROGRESS", assignee: "u2", updated_at: "2018-06-03 11:00" },

    // _conflict: giả lập có người khác vừa nhận trước (FRD F05-S03). Đơn MEDIUM vì Specialist không tự nhận HIGH (BRD 6.3).
    { order_id: "9b7a6c5d4e3f4a2b9c8d7e6f5a4b3c21", risk_score: 0.66, risk_level: "MEDIUM",
      top_factors: ["Seller took 2 days to hand over to the carrier", "Category Computers & accessories has a high low-rating rate"],
      seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories", customer_city: "Belo Horizonte", customer_state: "MG",
      order_value: 139.90, freight: 19.80,
      purchase_at: "2018-05-20", approved_at: "2018-05-20", carrier_at: "2018-05-22", delivered_at: "2018-06-01", estimated_at: "2018-06-09",
      queued_at: "2018-06-03 09:00", status: "PENDING", assignee: null, updated_at: "2018-06-03 09:00", _conflict: true },

    { order_id: "0e1f2a3b4c5d4e6f7a8b9c0d1e2f3a4b", risk_score: 0.63, risk_level: "MEDIUM",
      top_factors: ["New seller with fewer than 10 past orders", "Shipping fee higher than 55% of orders"],
      seller_id: "cc419e0650a3c5ba77189a1882b7556a", category: "health_beauty", customer_city: "Natal", customer_state: "RN",
      order_value: 88.50, freight: 21.90,
      purchase_at: "2018-05-21", approved_at: "2018-05-21", carrier_at: "2018-05-23", delivered_at: "2018-06-02", estimated_at: "2018-06-13",
      queued_at: "2018-06-03 13:00", status: "IN_PROGRESS", assignee: "u3", updated_at: "2018-06-04 08:40" },

    { order_id: "9e0f1a2b3c4d4e5f6a7b8c9d0e1f2a3b", risk_score: 0.61, risk_level: "MEDIUM",
      top_factors: ["Category Office furniture has a high low-rating rate"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "office_furniture", customer_city: "Campinas", customer_state: "SP",
      order_value: 205.00, freight: 18.40,
      purchase_at: "2018-05-25", approved_at: "2018-05-25", carrier_at: "2018-05-27", delivered_at: "2018-06-02", estimated_at: "2018-06-10",
      queued_at: "2018-06-04 10:30", status: "IN_PROGRESS", assignee: "u2", updated_at: "2018-06-04 10:35" },

    { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", risk_score: 0.58, risk_level: "MEDIUM",
      top_factors: ["Order has items from 2 different sellers", "Shipping fee higher than 60% of orders"],
      seller_id: "955fee9216a65b617aa5c0531780ce60", category: "housewares", customer_city: "Curitiba", customer_state: "PR",
      order_value: 97.50, freight: 24.40,
      purchase_at: "2018-05-17", approved_at: "2018-05-17", carrier_at: "2018-05-19", delivered_at: "2018-05-30", estimated_at: "2018-06-08",
      queued_at: "2018-06-01 08:00", status: "COMPLETED", assignee: "u1", outcome: "HAS_ISSUE", updated_at: "2018-06-01 15:10" },

    { order_id: "3f4a5b6c7d8e4f9a0b1c2d3e4f5a6b7c", risk_score: 0.55, risk_level: "MEDIUM",
      top_factors: ["Seller took 2 days to hand over to the carrier"],
      seller_id: "8b321bb669392f5163d04c59e235e066", category: "toys", customer_city: "Porto Alegre", customer_state: "RS",
      order_value: 64.90, freight: 17.30,
      purchase_at: "2018-05-23", approved_at: "2018-05-23", carrier_at: "2018-05-25", delivered_at: "2018-06-02", estimated_at: "2018-06-12",
      queued_at: "2018-06-04 08:00", status: "IN_PROGRESS", assignee: "u3", updated_at: "2018-06-04 08:15" },

    { order_id: "e8f7a6b5c4d34e2f1a0b9c8d7e6f5a43", risk_score: 0.52, risk_level: "MEDIUM",
      top_factors: ["New seller with fewer than 10 past orders"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "sports_leisure", customer_city: "Salvador", customer_state: "BA",
      order_value: 74.90, freight: 21.15,
      purchase_at: "2018-05-19", approved_at: "2018-05-19", carrier_at: "2018-05-21", delivered_at: "2018-06-02", estimated_at: "2018-06-11",
      queued_at: "2018-06-04 10:00", status: "PENDING", assignee: null, updated_at: "2018-06-04 10:00" },

    { order_id: "5d6e7f8091a24b3c4d5e6f7a8b9c0d1e", risk_score: 0.47, risk_level: "MEDIUM",
      top_factors: ["Shipping fee higher than 50% of orders"],
      seller_id: "955fee9216a65b617aa5c0531780ce60", category: "housewares", customer_city: "Florianópolis", customer_state: "SC",
      order_value: 56.00, freight: 19.70,
      purchase_at: "2018-05-24", approved_at: "2018-05-24", carrier_at: "2018-05-25", delivered_at: "2018-06-01", estimated_at: "2018-06-09",
      queued_at: "2018-06-04 09:00", status: "IN_PROGRESS", assignee: "u1", updated_at: "2018-06-04 09:05" },

    { order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", risk_score: 0.88, risk_level: "HIGH",
      top_factors: ["Seller took 5 days to hand over to the carrier", "Order value higher than 85% of orders"],
      seller_id: "7c67e1448b00f6e969d365cea6b010ab", category: "office_furniture", customer_city: "Rio de Janeiro", customer_state: "RJ",
      order_value: 512.00, freight: 48.00,
      purchase_at: "2018-05-02", approved_at: "2018-05-02", carrier_at: "2018-05-07", delivered_at: "2018-05-24", estimated_at: "2018-05-30",
      queued_at: "2018-05-25 09:00", status: "COMPLETED", assignee: "u2", outcome: "NO_ISSUE", updated_at: "2018-06-02 16:00", reopen_count: 1 },

    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", risk_score: 0.76, risk_level: "HIGH",
      top_factors: ["Seller–customer distance over 2,000 km", "Seller took 3 days to hand over to the carrier"],
      seller_id: "4a3ca9315b744ce9f8e9374361493884", category: "bed_bath_table", customer_city: "Belém", customer_state: "PA",
      order_value: 175.00, freight: 39.90,
      purchase_at: "2018-05-03", approved_at: "2018-05-03", carrier_at: "2018-05-06", delivered_at: "2018-05-25", estimated_at: "2018-06-01",
      queued_at: "2018-05-28 09:00", status: "SKIPPED", assignee: "u1", skip_reason: "UNREACHABLE", updated_at: "2018-05-30 10:20" },

    { order_id: "3a4b5c6d7e8f4a9b0c1d2e3f4a5b6c78", risk_score: 0.31, risk_level: "LOW",
      top_factors: ["No notable factor"],
      seller_id: "cc419e0650a3c5ba77189a1882b7556a", category: "health_beauty", customer_city: "Campinas", customer_state: "SP",
      order_value: 59.90, freight: 8.72,
      purchase_at: "2018-05-26", approved_at: "2018-05-26", carrier_at: "2018-05-27", delivered_at: "2018-06-01", estimated_at: "2018-06-15",
      queued_at: "2018-06-03 09:00", status: "PENDING", assignee: null, updated_at: "2018-06-03 09:00" },

    { order_id: "f0e1d2c3b4a54f6e7d8c9b0a1f2e3d4c", risk_score: 0.18, risk_level: "LOW",
      top_factors: ["No notable factor"],
      seller_id: "8b321bb669392f5163d04c59e235e066", category: "toys", customer_city: "Porto Alegre", customer_state: "RS",
      order_value: 45.00, freight: 15.23,
      purchase_at: "2018-05-18", approved_at: "2018-05-18", carrier_at: "2018-05-19", delivered_at: "2018-05-30", estimated_at: "2018-06-08",
      queued_at: "2018-06-01 10:00", status: "PENDING", assignee: null, updated_at: "2018-06-01 10:00" },

    { order_id: "c4d5e6f7a8b94c0d1e2f3a4b5c6d7e8f", risk_score: 0.41, risk_level: "LOW",
      top_factors: ["Category Computers & accessories has a high low-rating rate"],
      seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories", customer_city: "Belo Horizonte", customer_state: "MG",
      order_value: 139.90, freight: 19.80,
      purchase_at: "2018-05-20", approved_at: "2018-05-20", carrier_at: "2018-05-22", delivered_at: "2018-06-01", estimated_at: "2018-06-09",
      queued_at: "2018-06-03 09:05", status: "SKIPPED", assignee: "u2", skip_reason: "DUPLICATE", updated_at: "2018-06-03 14:00" },

    // Thiếu explanation: Order Detail phải hiện trạng thái rõ (FRD F04-S03)
    { order_id: "d8e9f0a1b2c34d5e6f7a8b9c0d1e2f3a", risk_score: 0.37, risk_level: "LOW",
      top_factors: [],
      seller_id: "955fee9216a65b617aa5c0531780ce60", category: "housewares", customer_city: "Santos", customer_state: "SP",
      order_value: 39.90, freight: 11.20,
      purchase_at: "2018-05-21", approved_at: "2018-05-21", carrier_at: "2018-05-22", delivered_at: "2018-05-29", estimated_at: "2018-06-06",
      queued_at: "2018-05-30 09:00", status: "COMPLETED", assignee: "u1", outcome: "NO_ISSUE", updated_at: "2018-05-31 11:00" }
  ];

  // ---------- Product Item Risk Output (BRD 6.1 mục 2–3, FRD F04-S03) ----------
  // Model chấm từng sản phẩm trong đơn; điểm của đơn = điểm sản phẩm cao nhất (aggregation rule "max-v1").
  // product_item_id = order_id + "-" + order_item_id (theo bảng order_items của Olist).
  // Chỉ dùng thuộc tính có trước mốc dự báo: ngành hàng, giá, phí ship, cân nặng, số ảnh.
  // synthetic: dữ liệu chi tiết sản phẩm giả lập vì dữ liệu gốc thiếu (BRD 4.1), giao diện phải gắn nhãn.
  var EXTRA_ITEMS = {
    "a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30": [
      { category: "office_furniture", price: 289.90, weight_g: 14200, photos: 2, score: 0.91, first: true },
      { category: "office_furniture", price: 129.00, weight_g: 6100, photos: 4, score: 0.62,
        factors: ["Heavy item shipped over 1,500 km"] },
      { category: "housewares", price: 41.00, weight_g: 900, photos: 1, score: 0.33, synthetic: true, factors: [] }
    ],
    "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47": [
      { category: "bed_bath_table", price: 139.00, weight_g: 2300, photos: 3, score: 0.84, first: true },
      { category: "bed_bath_table", price: 50.00, weight_g: 700, photos: 1, score: 0.58, synthetic: true,
        factors: ["Product has only 1 photo"] }
    ],
    "7f3e2a1b0c9d4e8f7a6b5c4d3e2f1a0b": [
      { category: "computers_accessories", price: 249.90, weight_g: 1800, photos: 2, score: 0.78, first: true },
      { category: "telephony", price: 62.50, weight_g: 300, photos: 5, score: 0.49,
        factors: ["Item ships from a second seller"] }
    ],
    "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a": [
      { category: "housewares", price: 59.50, weight_g: 1200, photos: 2, score: 0.58, first: true },
      { category: "garden_tools", price: 38.00, weight_g: 2600, photos: 1, score: 0.44,
        factors: ["Item ships from a second seller"] }
    ],
    "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d": [
      { category: "office_furniture", price: 389.00, weight_g: 15800, photos: 3, score: 0.72, first: true, synthetic: true }
    ]
  };
  function hexShift(id, n) {   // product_id giả nhưng cố định theo đơn
    var h = "0123456789abcdef", s = id.substring(8) + id.substring(0, 8), out = "";
    for (var k = 0; k < s.length; k++) out += h.charAt((h.indexOf(s.charAt(k)) + n) % 16);
    return out;
  }
  function levelOf(score) { return score >= threshold.high_from ? "HIGH" : (score >= threshold.medium_from ? "MEDIUM" : "LOW"); }

  for (var i = 0; i < cases.length; i++) {
    var c = cases[i];
    // Metadata model chung cho cả batch dự báo (FRD F04-S02)
    c.model_version = "hd-model v0.3 (LightGBM)";
    c.predicted_at = c.queued_at;
    c.aggregation_rule = "max-v1";
    if (c.reopen_count == null) c.reopen_count = 0;
    // Review Cycle (BRD 6.8): queued_at = mốc bắt đầu chu kỳ hiện tại; original_queued_at giữ lần vào queue đầu tiên
    c.cycle_no = c.reopen_count + 1;
    c.original_queued_at = c.queued_at;

    var defs = EXTRA_ITEMS[c.order_id] || [{ category: c.category, price: Math.round((c.order_value - 0) * 100) / 100, weight_g: 1500, photos: 2, score: c.risk_score, first: true }];
    c.items = [];
    for (var j = 0; j < defs.length; j++) {
      var d = defs[j];
      c.items.push({
        product_item_id: c.order_id + "-" + (j + 1),
        product_id: hexShift(c.order_id, j + 1),
        category: d.category, price: d.price, weight_g: d.weight_g, photos: d.photos,
        risk_score: d.score, risk_level: levelOf(d.score),
        top_factors: d.first ? c.top_factors : (d.factors || []),
        suggested_action: { HIGH: "CONTACT", MEDIUM: "MONITOR", LOW: "NO_ACTION" }[levelOf(d.score)],
        model_version: "hd-item v0.3 (LightGBM)", predicted_at: c.predicted_at,
        synthetic_data_flag: !!d.synthetic, data_source: d.synthetic ? "synthetic_v1" : "olist_order_items"
      });
    }
  }
  // Đơn 7a8b9c0d đã mở lại 1 lần: chu kỳ 2 bắt đầu lúc mở lại, lần vào queue đầu tiên vẫn là 25/05
  for (var r = 0; r < cases.length; r++) {
    if (cases[r].order_id == "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d") cases[r].queued_at = "2018-06-02 09:00";
  }

  // ---------- Review Activity: mỗi lần liên lạc (BRD 6.6) ----------
  // cycle: chu kỳ xử lý (mặc định 1). evidence: minh chứng đã liên lạc (feedback 13/10, chờ BA đưa vào FRD).
  var contacts = [
    { order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", at: "2018-06-04 11:30", user: "u2", method: "PHONE", result: "NO_ANSWER",
      note: "Called twice, no answer", next_date: "2018-06-05",
      evidence: [{ file_name: "call-log-0604-1130.png", file_type: "image/png", file_size: 84210 }], evidence_ref: "Call log #CL-20180604-117" },

    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-01 10:00", user: "u3", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-06-04" },
    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-02 10:30", user: "u3", method: "PHONE", result: "NO_ANSWER", note: "Number unreachable", next_date: "2018-06-03" },
    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-03 10:00", user: "u3", method: "EMAIL", result: "NO_ANSWER", note: "Email sent, no reply", next_date: "" },

    { order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", at: "2018-06-04 10:00", user: "u3", method: "PHONE", result: "REACHED",
      note: "Customer says the chair looks a bit different from the photo; call back after assembly", next_date: "2018-06-05" },

    { order_id: "4c5d6e7f8a9b4c0d1e2f3a4b5c6d7e8f", at: "2018-06-03 11:00", user: "u2", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-06-04" },

    { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", at: "2018-06-01 15:00", user: "u1", method: "PHONE", result: "REACHED",
      note: "Customer complained about dented packaging; forwarded to seller", next_date: "" },

    { order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", at: "2018-05-26 10:00", user: "u2", method: "PHONE", result: "REACHED",
      note: "Customer says the desk is fine", next_date: "", cycle: 1 },
    { order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", at: "2018-06-02 15:30", user: "u2", method: "PHONE", result: "REACHED",
      note: "Customer is satisfied, only asked about warranty", next_date: "", cycle: 2,
      evidence: [{ file_name: "email-confirmation.pdf", file_type: "application/pdf", file_size: 120330 }], evidence_ref: "" },

    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-28 10:00", user: "u1", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-05-29" },
    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-29 10:00", user: "u1", method: "MESSAGE", result: "NO_ANSWER", note: "", next_date: "2018-05-30" },
    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-30 10:00", user: "u1", method: "PHONE", result: "WRONG_NUMBER", note: "Wrong phone number", next_date: "" }
  ];

  // ---------- Audit Event (BRD 6.8): không ai sửa/xoá ----------
  // type: CLAIM, ASSIGN, REASSIGN, STATUS, CONTACT, SKIP, REOPEN, OVERRIDE, MODEL_NOTE
  var audits = [
    { at: "2018-05-25 10:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-05-28 16:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · NO_ISSUE", reason: "" },
    { at: "2018-05-28 09:10", actor: "u1", order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-05-30 10:20", actor: "u1", order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", type: "SKIP", old_value: "IN_PROGRESS", new_value: "SKIPPED", reason: "Unreachable after 3 attempts" },
    { at: "2018-05-30 09:30", actor: "u1", order_id: "d8e9f0a1b2c34d5e6f7a8b9c0d1e2f3a", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-05-31 11:00", actor: "u1", order_id: "d8e9f0a1b2c34d5e6f7a8b9c0d1e2f3a", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · NO_ISSUE", reason: "" },
    { at: "2018-06-01 08:20", actor: "u1", order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-06-01 15:10", actor: "u1", order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · HAS_ISSUE", reason: "" },
    { at: "2018-06-01 09:40", actor: "u3", order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Lê Văn C", reason: "" },
    { at: "2018-06-02 09:00", actor: "u4", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "REOPEN", old_value: "COMPLETED", new_value: "PENDING", reason: "Customer emailed another complaint after the case was closed" },
    { at: "2018-06-02 09:30", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-02 16:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · NO_ISSUE", reason: "" },
    { at: "2018-06-02 10:10", actor: "u2", order_id: "4c5d6e7f8a9b4c0d1e2f3a4b5c6d7e8f", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-03 13:20", actor: "u3", order_id: "0e1f2a3b4c5d4e6f7a8b9c0d1e2f3a4b", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Lê Văn C", reason: "" },
    { at: "2018-06-03 09:20", actor: "u2", order_id: "c4d5e6f7a8b94c0d1e2f3a4b5c6d7e8f", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-03 14:00", actor: "u2", order_id: "c4d5e6f7a8b94c0d1e2f3a4b5c6d7e8f", type: "SKIP", old_value: "IN_PROGRESS", new_value: "SKIPPED", reason: "Duplicate of order 9b7a6c5d" },
    { at: "2018-06-04 07:30", actor: "u2", order_id: "8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-04 09:20", actor: "u4", order_id: "8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f", type: "REASSIGN", old_value: "Trần Thị B", new_value: "Lê Văn C", reason: "B is off this afternoon; C knows customers in the North region" },
    { at: "2018-06-04 08:10", actor: "u4", order_id: "3f4a5b6c7d8e4f9a0b1c2d3e4f5a6b7c", type: "ASSIGN", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Lê Văn C", reason: "" },
    { at: "2018-06-04 09:05", actor: "u1", order_id: "5d6e7f8091a24b3c4d5e6f7a8b9c0d1e", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-06-04 09:35", actor: "u4", order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", type: "ASSIGN", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Lê Văn C", reason: "" },
    { at: "2018-06-04 10:35", actor: "u2", order_id: "9e0f1a2b3c4d4e5f6a7b8c9d0e1f2a3b", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-04 11:05", actor: "u2", order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-04 11:30", actor: "u2", order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", type: "CONTACT", old_value: "0/3", new_value: "1/3 · NO_ANSWER", reason: "" },
    { at: "2018-06-04 12:00", actor: "u4", order_id: "a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30", type: "MODEL_NOTE", old_value: "", new_value: "Flagged for model review", reason: "High score, but this seller has improved handover time over the last 2 weeks" }
  ];

  for (var q = 0; q < contacts.length; q++) {
    if (contacts[q].cycle == null) contacts[q].cycle = 1;
    if (contacts[q].evidence == null) contacts[q].evidence = [];
    if (contacts[q].evidence_ref == null) contacts[q].evidence_ref = "";
  }

  // ---------- Nhận xét trên case (feedback 13/10: "nhận xét của nhân viên và quản lý") ----------
  // Khác ghi chú của lần liên lạc (lời khách) và ghi chú model (gửi nhóm ML): đây là đánh giá nội bộ về case.
  var comments = [
    { order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", at: "2018-06-04 10:05", user: "u3",
      text: "Customer sounds unsure about the chair colour. Worth checking the seller's photos." },
    { order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", at: "2018-06-04 10:40", user: "u4",
      text: "Agree. Call back after assembly as planned; if colour is wrong, offer to open a return request." },
    { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", at: "2018-06-01 15:05", user: "u1",
      text: "Packaging dented on arrival. Product works, customer still annoyed." }
  ];

  // ---------- Quyết định của Manager (feedback 13/10: trang Decision) ----------
  // decision: NO_FURTHER_ACTION | FOLLOW_UP_CUSTOMER | WORK_WITH_SELLER | REFER_AFTER_SALES
  var decisions = [
    { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", at: "2018-06-01 16:30", actor: "u4", cycle: 1, decision: "WORK_WITH_SELLER",
      next_step: "Send the packaging photos to seller 955fee92 and ask for better padding on housewares orders.", due_date: "2018-06-06",
      note: "Second packaging complaint for this seller this month." }
  ];

  return { now: now, threshold: threshold, param_defs: PARAM_DEFS, params: params, users: users, accounts: accounts,
    cases: cases, contacts: contacts, audits: audits, comments: comments, decisions: decisions };
})();
