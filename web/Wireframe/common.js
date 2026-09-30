// =========================================================
// common.js — hàm dùng chung cho cả 4 màn
// =========================================================

// Bật/tắt các ô ghi chú màu vàng
function toggleNotes() {
  document.body.classList.toggle("hide-notes");
}

// Tìm một đơn trong mảng orders theo order_id
function findOrder(id) {
  for (var i = 0; i < orders.length; i++) {
    if (orders[i].order_id == id) {
      return orders[i];
    }
  }
  return null;
}

// Nhãn mức rủi ro
function badge(level) {
  return '<span class="badge ' + level + '">' + level + "</span>";
}

// Rút gọn order_id dài 32 ký tự cho dễ nhìn
function shortId(id) {
  return id.substring(0, 8) + "…";
}

// Số ngày giữa hai ngày dạng "YYYY-MM-DD"
function daysBetween(a, b) {
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}
