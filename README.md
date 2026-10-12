# Hidden Dissatisfaction

## 1. Tải dataset (bắt buộc)

Dữ liệu **không nằm trong repo** (khoảng 123 MB, đã được `.gitignore`). Bạn phải tự tải trước khi chạy bất kỳ notebook nào.

1. Tải **Brazilian E-Commerce Public Dataset by Olist** từ Kaggle:
   <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
2. Giải nén và đặt 9 file CSV vào `notebooks/dataset/`, giữ nguyên tên file.

Hoặc dùng Kaggle CLI, chạy từ thư mục gốc của repo:

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p notebooks/dataset --unzip
```

### Cấu trúc thư mục cần có

```
Hidden-Dissatisfaction/
├── README.md
├── pyproject.toml
└── notebooks/
    ├── olist_open_eda.ipynb
    ├── 01_eda_why_lateness_dominates.ipynb
    ├── 02_modelling_dataset.ipynb
    ├── figures/                                   # hình do olist_open_eda xuất ra
    └── dataset/
        ├── about_dataset.md
        ├── image.png                              # sơ đồ schema
        ├── olist_customers_dataset.csv            # ┐
        ├── olist_geolocation_dataset.csv          # │
        ├── olist_order_items_dataset.csv          # │
        ├── olist_order_payments_dataset.csv       # │
        ├── olist_order_reviews_dataset.csv        # ├ 9 file tải từ Kaggle
        ├── olist_orders_dataset.csv               # │
        ├── olist_products_dataset.csv             # │
        ├── olist_sellers_dataset.csv              # │
        ├── product_category_name_translation.csv  # ┘
        └── modelling_orders.parquet               # do notebook 02 tạo ra
```

Cả ba notebook đọc dữ liệu qua đường dẫn tương đối `dataset/`. Đặt sai chỗ hoặc đổi tên file thì notebook báo `FileNotFoundError` ngay ở cell load dữ liệu.

## 2. Cài môi trường

Cần Python 3.11 và [uv](https://docs.astral.sh/uv/). `uv.lock` là nguồn phiên bản dependency
thống nhất cho toàn nhóm.

```bash
uv python install 3.11
uv sync --frozen --extra ml --extra notebook --extra dev
```

## 3. Chạy notebook

Chạy theo thứ tự dưới đây. Mở bằng Jupyter hoặc VS Code rồi *Run All*, hoặc chạy bằng dòng lệnh từ thư mục gốc của repo:

```bash
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/02_modelling_dataset.ipynb
```

| Thứ tự | Notebook | Nội dung | Kết quả |
|---|---|---|---|
| 1 | `olist_open_eda.ipynb` | EDA tổng quát cho 9 bảng: grain, join, missingness, outlier, phân phối, tương quan | 16 hình trong `notebooks/figures/` |
| 2 | `01_eda_why_lateness_dominates.ipynb` | Vì sao các mô hình đều "phát hiện" lateness, và nhóm on-time-but-unhappy bị bỏ sót | Lý do chỉ mô hình hoá đơn giao đúng hạn |
| 3 | `02_modelling_dataset.ipynb` | Dựng bảng modelling và kiểm tra chất lượng: nhãn, giá trị phi logic, missingness, leakage, chia tập | `notebooks/dataset/modelling_orders.parquet` |

## 4. Bảng modelling

`modelling_orders.parquet` có 89,182 dòng và 35 cột, mỗi dòng là một đơn hàng. Data dictionary đầy đủ nằm ở §10 của notebook `02`.

| Mục | Định nghĩa |
|---|---|
| Quần thể | Đơn đã giao, có review, mua từ 01/2017 đến 08/2018, giao **đúng hạn** |
| Thời điểm dự đoán | Lúc đơn được giao |
| Target | `negative` = `review_score` là 1 hoặc 2 sao (9.2% số đơn) |
| Chia tập (cột `split`) | Theo ngày mua: train 01–12/2017, validation 01–03/2018, test 04–08/2018 |

| Tập | Số đơn | Tỉ lệ tiêu cực |
|---|---:|---:|
| train | 40,714 | 9.2% |
| validation | 17,864 | 10.5% |
| test | 30,604 | 8.6% |

Lưu ý khi modelling:

- Không dùng `main_seller` hay `customer_unique_id` làm feature; đó là khoá. 20.6% đơn test đến từ seller chưa xuất hiện trước đó.
- Review text và các mốc thời gian review chỉ có sau khi có nhãn, nên không được làm feature.
- Encoder, imputer, scaler chỉ fit trên train; tune trên validation; test chỉ dùng một lần.
- Đánh giá bằng PR-AUC và precision/recall tại top-k, không dùng accuracy.
Research codebase for identifying **1–2 star reviews among Olist orders delivered on time or early**. The prediction point is immediately after delivery confirmation and before review creation.

The project supports diagnosis and budgeted case prioritization. It does **not** claim that a voucher, refund, or customer contact causes a better outcome.

## Research scope

- **Population:** delivered orders where `order_delivered_customer_date <= order_estimated_delivery_date`.
- **Primary outcome:** review score 1–2 among orders with an observed review.
- **Secondary outcome:** whether an order receives a review.
- **Validation:** temporal holdout or rolling-origin evaluation; random split is not the primary result.
- **Primary metrics:** PR-AUC, minority recall/precision, Brier score, calibration, and recall/value captured at 5%, 10%, and 20% budgets.
- **Decision baselines:** random, value-only, risk-only, and risk × value.

See [`docs/research-design.md`](docs/research-design.md) for the complete methodological contract.

## Repository layout

```text
.
├── configs/                    # Versioned experiment configuration
├── data/                       # Local-only raw/interim/processed data
├── docs/                       # Architecture, contracts, and research design
├── notebooks/                  # Exploration and report-oriented analyses
├── src/hidden_dissatisfaction/
│   ├── domain/                 # Pure research rules and invariants
│   ├── application/            # Use cases and ports
│   ├── infrastructure/         # Dataset/model/artifact adapters
│   └── interfaces/             # CLI now; API may be added when required
├── tests/                      # Unit, integration, and acceptance tests
├── artifacts/                  # Generated models and predictions (ignored)
├── reports/                    # Versioned tables/figures intended for reports
└── web/Wireframe/              # Existing static product wireframe
```

Dependency direction:

```text
interfaces ──> application ──> domain
                    ^
                    │
              infrastructure
```

The domain does not import pandas, scikit-learn, web frameworks, or storage SDKs.

## Setup

Python 3.11 and [uv](https://docs.astral.sh/uv/) are required. The committed lockfile is the
authoritative dependency resolution for local development and CI.

```bash
uv python install 3.11
uv sync --frozen --extra ml --extra notebook --extra dev
```

Place the nine Olist CSV files in `data/raw/olist/`. Raw data is intentionally excluded from Git.

## Quality gates

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

Run the initial vertical slice:

```bash
hidden-dissatisfaction assess-order \
  --order-id demo-001 \
  --delivered-at 2018-01-10T10:00:00 \
  --estimated-at 2018-01-12T00:00:00 \
  --review-score 2 \
  --review-created-at 2018-01-11T00:00:00
```

## Development order

Build one end-to-end research slice at a time:

1. define the domain rule and data contract;
2. define the application port/use case;
3. implement the Olist adapter;
4. expose it through CLI/notebook;
5. add unit and integration tests;
6. record experiment configuration and generated evidence.

Read [`AGENTS.md`](AGENTS.md) before adding code.
