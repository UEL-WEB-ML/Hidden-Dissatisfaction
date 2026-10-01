// =========================================================
// common.js — hàm dùng chung cho mọi màn
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

// Người đang đăng nhập: màn Đăng nhập lưu tên và vai vào trình duyệt (localStorage)
function showUser() {
  var name = localStorage.getItem("userName");
  var role = localStorage.getItem("userRole");
  var box = document.getElementById("user-box");
  if (name != null && box != null) {
    box.innerHTML = (role == "manager" ? "Quản lý: " : "Nhân viên: ") + name
      + ' · <a href="login.html" onclick="logout()">Đăng xuất</a>';
  }
  // Quản lý thì hiện thêm link Overview trên thanh điều hướng
  if (role == "manager") {
    document.body.classList.add("is-manager");
  }
}

function logout() {
  localStorage.removeItem("userName");
  localStorage.removeItem("userRole");
}

showUser();
