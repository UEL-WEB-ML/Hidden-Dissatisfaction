// =========================================================
// mock-data.js
// DỮ LIỆU GIẢ cho backend giả (mock-server.js), bám theo logical data object của FRD mục 4.1:
//   Order Risk Case · Review Assignment · Review Status · Review Activity
//   Review Outcome · Audit Event · User/Role · Threshold Configuration
// Frontend KHÔNG đọc file này trực tiếp; mọi dữ liệu đi qua js/api.js theo API_CONTRACT_olist_hidden_dissatisfaction.md.
// Khi có backend thật thì bỏ file này cùng mock-server.js.
// =========================================================

var MOCK_DB = (function () {

  // Thời điểm "hiện tại" giả lập (thứ Hai 04/06/2018) để tính SLA, aging cho ổn định khi xem prototype
  var now = "2018-06-04 14:00";

  // ---------- Threshold Configuration (BRD 6.3, 6.6, 6.7) ----------
  // Initial configuration, có version. Bản thật đọc từ backend, đổi phải có owner + lịch sử.
  var config = {
    version: "cfg-v1 (effective 2018-05-01, owner: Product Owner)",
    threshold_version: "thr-v1",
    high_from: 0.70,          // score >= 0.70 → HIGH
    medium_from: 0.45,        // 0.45 <= score < 0.70 → MEDIUM, còn lại LOW
    capacity: 5,              // tối đa 5 active orders / Specialist
    capacity_warn: 4,         // từ đơn thứ 4 hiện cảnh báo
    max_contact: 3,           // tối đa 3 lần liên lạc
    retry_gap_days: 1,        // cách nhau 1 ngày làm việc
    sla_hours: { HIGH: 4, MEDIUM: 24, LOW: 48 },   // prototype tính theo giờ đồng hồ; bản thật theo business calendar
    soon_hours: 2,            // còn dưới 2 giờ → "Sắp quá hạn"
    stale_hours: 24,          // IN_PROGRESS 1 ngày không cập nhật → cảnh báo Manager
    aging_days: 2,            // nằm queue 2 ngày → escalation queue
    reopen_review_days: 7,    // mở lại sau 7 ngày ...
    reopen_review_times: 2    // ... hoặc quá 2 lần → Manager review bắt buộc
  };

  // ---------- User/Role ----------
  var users = [
    { id: "u1", full_name: "Nguyễn Văn A", role: "SPECIALIST" },
    { id: "u2", full_name: "Trần Thị B",   role: "SPECIALIST" },
    { id: "u3", full_name: "Lê Văn C",     role: "SPECIALIST" },
    { id: "u4", full_name: "Phạm Văn D",   role: "MANAGER" }
  ];

  // Tài khoản mẫu: tạo sẵn, không có đăng ký.
  // Bản thật: mật khẩu được mã hoá và kiểm tra ở máy chủ, không để trong file JS như thế này.
  var accounts = [
    { username: "nhanvien",  password: "123456", user_id: "u2" },   // Specialist đang giữ 3/5
    { username: "nhanvien2", password: "123456", user_id: "u3" },   // Specialist đã đủ 5/5
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
    // _conflict: giả lập có người khác vừa nhận trước (FRD F05-S03).
    { order_id: "7f3e2a1b0c9d4e8f7a6b5c4d3e2f1a0b", risk_score: 0.78, risk_level: "HIGH",
      top_factors: ["Order has items from 2 different sellers", "Category Computers & accessories has a high low-rating rate"],
      seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories", customer_city: "Belo Horizonte", customer_state: "MG",
      order_value: 312.40, freight: 27.90,
      purchase_at: "2018-05-22", approved_at: "2018-05-22", carrier_at: "2018-05-24", delivered_at: "2018-06-03", estimated_at: "2018-06-08",
      queued_at: "2018-06-04 10:45", status: "PENDING", assignee: null, updated_at: "2018-06-04 10:45", _conflict: true },

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

    { order_id: "9b7a6c5d4e3f4a2b9c8d7e6f5a4b3c21", risk_score: 0.66, risk_level: "MEDIUM",
      top_factors: ["Seller took 2 days to hand over to the carrier", "Category Computers & accessories has a high low-rating rate"],
      seller_id: "da8622b14eb17ae2831f4ac5b9dab84a", category: "computers_accessories", customer_city: "Belo Horizonte", customer_state: "MG",
      order_value: 139.90, freight: 19.80,
      purchase_at: "2018-05-20", approved_at: "2018-05-20", carrier_at: "2018-05-22", delivered_at: "2018-06-01", estimated_at: "2018-06-09",
      queued_at: "2018-06-03 09:00", status: "PENDING", assignee: null, updated_at: "2018-06-03 09:00" },

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

  // Metadata model chung cho cả batch dự báo (FRD F04-S02)
  for (var i = 0; i < cases.length; i++) {
    cases[i].model_version = "hd-model v0.3 (LightGBM)";
    cases[i].predicted_at = cases[i].queued_at;
    if (cases[i].reopen_count == null) cases[i].reopen_count = 0;
  }

  // ---------- Review Activity: mỗi lần liên lạc (BRD 6.6) ----------
  var contacts = [
    { order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", at: "2018-06-04 11:30", user: "u2", method: "PHONE", result: "NO_ANSWER",
      note: "Called twice, no answer", next_date: "2018-06-05" },

    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-01 10:00", user: "u3", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-06-04" },
    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-02 10:30", user: "u3", method: "PHONE", result: "NO_ANSWER", note: "Number unreachable", next_date: "2018-06-03" },
    { order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", at: "2018-06-03 10:00", user: "u3", method: "EMAIL", result: "NO_ANSWER", note: "Email sent, no reply", next_date: "" },

    { order_id: "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d", at: "2018-06-04 10:00", user: "u3", method: "PHONE", result: "REACHED",
      note: "Customer says the chair looks a bit different from the photo; call back after assembly", next_date: "2018-06-05" },

    { order_id: "4c5d6e7f8a9b4c0d1e2f3a4b5c6d7e8f", at: "2018-06-03 11:00", user: "u2", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-06-04" },

    { order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", at: "2018-06-01 15:00", user: "u1", method: "PHONE", result: "REACHED",
      note: "Customer complained about dented packaging; forwarded to seller", next_date: "" },

    { order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", at: "2018-06-02 15:30", user: "u2", method: "PHONE", result: "REACHED",
      note: "Customer is satisfied, only asked about warranty", next_date: "" },

    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-28 10:00", user: "u1", method: "PHONE", result: "NO_ANSWER", note: "", next_date: "2018-05-29" },
    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-29 10:00", user: "u1", method: "MESSAGE", result: "NO_ANSWER", note: "", next_date: "2018-05-30" },
    { order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", at: "2018-05-30 10:00", user: "u1", method: "PHONE", result: "WRONG_NUMBER", note: "Wrong phone number", next_date: "" }
  ];

  // ---------- Audit Event (BRD 6.8): không ai sửa/xoá ----------
  // type: CLAIM, ASSIGN, REASSIGN, STATUS, CONTACT, SKIP, REOPEN, OVERRIDE, MODEL_NOTE
  var audits = [
    { at: "2018-05-25 10:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-05-28 16:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · No issue", reason: "" },
    { at: "2018-05-28 09:10", actor: "u1", order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-05-30 10:20", actor: "u1", order_id: "b1c2d3e4f5a64b7c8d9e0f1a2b3c4d5e", type: "SKIP", old_value: "IN_PROGRESS", new_value: "SKIPPED", reason: "Unreachable after 3 attempts" },
    { at: "2018-05-30 09:30", actor: "u1", order_id: "d8e9f0a1b2c34d5e6f7a8b9c0d1e2f3a", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-05-31 11:00", actor: "u1", order_id: "d8e9f0a1b2c34d5e6f7a8b9c0d1e2f3a", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · No issue", reason: "" },
    { at: "2018-06-01 08:20", actor: "u1", order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" },
    { at: "2018-06-01 15:10", actor: "u1", order_id: "1d2c3b4a5f6e4d7c8b9a0f1e2d3c4b5a", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · Issue found", reason: "" },
    { at: "2018-06-01 09:40", actor: "u3", order_id: "2b4d6f8a0c1e4a3b5d7f9a1c3e5b7d90", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Lê Văn C", reason: "" },
    { at: "2018-06-02 09:00", actor: "u4", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "REOPEN", old_value: "COMPLETED", new_value: "PENDING", reason: "Customer emailed another complaint after the case was closed" },
    { at: "2018-06-02 09:30", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Trần Thị B", reason: "" },
    { at: "2018-06-02 16:00", actor: "u2", order_id: "7a8b9c0d1e2f4a3b4c5d6e7f8a9b0c1d", type: "STATUS", old_value: "IN_PROGRESS", new_value: "COMPLETED · No issue", reason: "" },
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
    { at: "2018-06-04 11:30", actor: "u2", order_id: "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47", type: "CONTACT", old_value: "0/3", new_value: "1/3 · No answer", reason: "" },
    { at: "2018-06-04 12:00", actor: "u4", order_id: "a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30", type: "MODEL_NOTE", old_value: "", new_value: "Flagged for model review", reason: "High score, but this seller has improved handover time over the last 2 weeks" }
  ];

  return { now: now, config: config, users: users, accounts: accounts, cases: cases, contacts: contacts, audits: audits };
})();
