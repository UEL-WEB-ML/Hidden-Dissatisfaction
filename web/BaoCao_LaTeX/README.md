# Báo cáo đồ án môn Phát triển Web Kinh doanh

**Đề tài:** Xây dựng hệ thống web hỗ trợ phát hiện và xử lý đơn hàng có nguy cơ không hài lòng ẩn
**GVHD:** TS. Trần Duy Thanh · **Nhóm 1** · Dữ liệu: Brazilian E-Commerce Public Dataset by Olist

Thư mục này chứa mã nguồn LaTeX của báo cáo. File nộp cuối cùng là `main.pdf`.

Đồ án dùng chung một hệ thống với môn Machine Learning. Báo cáo này chỉ viết phần thuộc môn Web:
phân tích thiết kế hệ thống, giao diện, lưu hành động của người dùng. Phần huấn luyện mô hình
thuộc báo cáo môn ML, ở đây chỉ nhắc đến như dữ liệu đầu vào của hệ thống.

## Ai viết file nào

| File | Nội dung | Người viết |
|---|---|---|
| `main.tex` | File gốc, gọi các file khác |  **không sửa** |
| `settings.tex` | Định dạng chung (lề, font, số mục, trích dẫn) | Trúc |
| `bia.tex`, `bia-thong-tin.tex` | Bìa theo mẫu UEL | Trúc |
| `thanh-vien.tex` | Danh sách thành viên, bảng phân công | Trúc |
| `loi-cam-on.tex` | Lời cảm ơn, lời cam kết | Trúc |
| `tailieu.bib` | Danh mục tài liệu tham khảo | Ai trích tài liệu mới thì thêm vào cuối file |
| `chuong/00-tom-tat.tex` | Tóm tắt (viết sau cùng) | Trúc |
| `chuong/01-gioi-thieu.tex` | Mục 1. Giới thiệu | Trúc |
| `chuong/02-co-so-ly-thuyet.tex` | Mục 2. Cơ sở lý thuyết (viết cuối) | Trân |
| `chuong/03-phuong-phap.tex` | Mục 3. Phương pháp thực hiện | 3.1 Huy + Trân · 3.2 Quân · 3.3 Trung · 3.4 Huy |
| `chuong/04-ket-qua.tex` | Mục 4. Kết quả và phân tích | 4.1 Trúc + Quân · 4.2 Trân |
| `chuong/05-thao-luan.tex` | Mục 5. Thảo luận | Huy |
| `chuong/06-ket-luan.tex` | Mục 6. Kết luận và đề xuất | Trúc |
| (tự sinh từ `tailieu.bib`) | Mục 7. Tài liệu tham khảo | |
| `chuong/08-phu-luc.tex` | Mục 8. Phụ lục | Trung |
| `hinh/` | Ảnh chụp màn hình, sơ đồ | Ai có hình thì thêm vào |

Trong mỗi file, chỗ chữ xám nghiêng trong ngoặc vuông là gợi ý cần viết gì. Viết xong thì xóa
dòng `\placeholder{...}` đó đi.

## Cách viết phần của mình

Có 2 cách, chọn cách nào cũng được:

1. **Không rành LaTeX:** viết bằng Word hoặc Google Docs, gửi Trúc dán vào file `.tex`.
2. **Viết thẳng vào file `.tex`:** mở file của mình trong thư mục `chuong/`, thay phần
   `\placeholder{...}` bằng nội dung. Văn xuôi thì gõ như bình thường, mỗi đoạn cách nhau một dòng trống.

Mấy cú pháp hay dùng:

```latex
\subsection{Tên tiểu mục}            % tiêu đề 3.1, 3.2...
\textbf{chữ đậm}   \textit{chữ nghiêng}

\begin{itemize}                        % gạch đầu dòng
    \item Ý thứ nhất
    \item Ý thứ hai
\end{itemize}

\parencite{ravula2023}                 % trích dẫn dạng (Ravula, 2023)
\textcite{ravula2023}                  % trích dẫn dạng Ravula (2023)

\begin{figure}[H]                      % chèn hình
    \centering
    \includegraphics[width=0.9\textwidth]{hinh/risk-queue-desktop.png}
    \caption{Màn hình danh sách đơn cần ưu tiên}
    \label{fig:risk-queue}
\end{figure}
```

Ký tự `%`, `&`, `_`, `#` trong văn bản phải thêm dấu `\` phía trước: `9,27\%`, `R\&D`, `order\_id`.

## Quy ước chung

- **Ai sửa file nấy.** File `03` và `04` có nhiều người viết: chỉ sửa đúng tiểu mục ghi tên mình.
- **Không sửa `main.tex` và `settings.tex`.** Cần đổi gì thì báo Trúc.
- **Tên ảnh không dấu, không khoảng trắng:** `risk-queue-desktop.png`, không phải `Màn hình 1.png`.
- **Tài liệu tham khảo:** ưu tiên từ năm 2021 trở đi; không dùng MDPI, Frontiers, Hindawi
  (thầy cấm). Trích theo chuẩn APA, khai báo trong `tailieu.bib`.
- **Không chép câu chữ từ báo cáo môn ML.** Số liệu giống nhau là bình thường, lời văn phải khác.
- **Số liệu Olist** lấy theo BRD của nhóm, không tự đếm lại theo cách khác.
- Nếu máy biên dịch được thì chạy thử trước khi đẩy lên. Nếu không thì cứ đẩy rồi nhắn Trúc kiểm tra.

## Biên dịch ra PDF

Cần có XeLaTeX và biber. Không bắt buộc ai cũng phải biên dịch: nếu chỉ viết nội dung thì
sửa file `.tex` của mình rồi đẩy lên, Trúc biên dịch và kiểm tra.

### Windows

1. Cài **MiKTeX** tại https://miktex.org/download (bấm Next đến hết). Ở bước
   "Install missing packages on-the-fly" chọn **Yes** để MiKTeX tự tải gói còn thiếu.
   MiKTeX đã có sẵn XeLaTeX và biber.
2. Mở thư mục này trong File Explorer, bấm vào thanh địa chỉ, gõ `cmd` rồi Enter.
3. Chạy lần lượt 4 lệnh:

```bat
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

Lần đầu chạy sẽ lâu vì MiKTeX tải gói. Xong thì mở `main.pdf` để xem.

Chạy 4 lần là vì: lần 1 ghi lại các trích dẫn, `biber` tạo danh mục tài liệu tham khảo,
hai lần sau đưa trích dẫn và số trang mục lục vào đúng chỗ. Nếu chỉ sửa chữ, không thêm
trích dẫn hay mục mới, chạy `xelatex main.tex` một lần là đủ.

Nếu máy đã cài Git for Windows thì có thể mở **Git Bash** trong thư mục này và chạy
`bash build.sh` như trên Ubuntu.

Dùng VS Code thì cài thêm tiện ích **LaTeX Workshop** để xem PDF ngay bên cạnh; dùng TeXworks
(đi kèm MiKTeX) thì chọn **XeLaTeX** ở ô cạnh nút chạy màu xanh.

### Ubuntu

```bash
sudo apt install texlive-xetex texlive-lang-other texlive-latex-extra texlive-bibtex-extra biber
```

Mở terminal trong thư mục này rồi chạy **một trong hai** lệnh:

```bash
bash build.sh        # cách 1
./build.sh           # cách 2 (file đã có quyền chạy)
```

Kết quả: in ra `Xong, 0 loi -> main.pdf` là được. Nếu có lỗi, script in ra các dòng lỗi.

### macOS

Cài MacTeX (https://tug.org/mactex), sau đó chạy `bash build.sh` trong Terminal.

### Không muốn cài gì

Dùng Overleaf để xem thử: nén thư mục này lại, chọn New Project → Upload Project, rồi vào
Menu → Compiler chọn **XeLaTeX**. Bản miễn phí chỉ cho 1 người cùng sửa và hay hết thời gian
biên dịch, nên Overleaf chỉ để xem thử, bản chính vẫn là thư mục này trên GitHub.

### Lỗi hay gặp

| Thông báo | Nguyên nhân | Cách sửa |
|---|---|---|
| `Undefined control sequence` | Gõ sai tên lệnh, hoặc thiếu dấu `\` trước `%`, `_`, `&` | Xem số dòng trong thông báo, sửa đúng dòng đó |
| `Missing $ inserted` | Dùng `_` hoặc `^` ngoài công thức | Viết `order\_id` thay cho `order_id` |
| `File ... not found` | Sai tên hoặc sai đường dẫn ảnh | Ảnh phải nằm trong `hinh/`, tên không dấu |
| Trích dẫn hiện chữ đậm `ravula2023` thay vì (Ravula, 2023) | Chưa chạy `biber`, hoặc sai khóa trích dẫn | Chạy đủ 4 lệnh; kiểm tra khóa có trong `tailieu.bib` |
| Dùng `pdflatex` bị lỗi font | Báo cáo dùng font Unicode | Phải dùng `xelatex` |

## Làm việc với GitHub

```bash
git pull                                   # lấy bản mới nhất TRƯỚC khi sửa
# ... sửa file của mình ...
git add chuong/02-co-so-ly-thuyet.tex      # chỉ thêm file mình sửa
git commit -m "Viet muc 2.1"
git push
```

Không rành lệnh git thì dùng **GitHub Desktop** (https://desktop.github.com): Fetch/Pull,
sửa file, tick đúng file của mình, Commit, Push. Cũng có thể sửa thẳng trên trang GitHub
bằng nút hình cây bút ở góc phải file.

File tạm (`.aux`, `.log`, `.bbl`...) đã được bỏ qua trong `.gitignore`, không cần đẩy lên.

## Cấu trúc thư mục

```
main.tex                  file gốc
settings.tex              định dạng chung
bia.tex                   trang bìa
bia-thong-tin.tex         thông tin điền lên bìa
thanh-vien.tex            danh sách thành viên + phân công
loi-cam-on.tex            lời cảm ơn + lời cam kết
tailieu.bib               tài liệu tham khảo
chuong/                   nội dung từng mục
hinh/                     ảnh và sơ đồ
build.sh                  script biên dịch
main.pdf                  bản PDF mới nhất
```

## Tài liệu liên quan

- Bảng phân công và deadline: Google Sheet `WEB`, tab CHECKLIST
- Wireframe: file Figma của nhóm (3 trang Desktop, iPad, Phone)
- Tài liệu phân tích nghiệp vụ (BRD, FRD): dùng chung với môn ML
