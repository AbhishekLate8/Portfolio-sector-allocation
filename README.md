# Portfolio Sector Allocation API

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://portfolio-sector-allocation.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-85EA2D?style=flat&logo=swagger&logoColor=black)](https://portfolio-sector-allocation.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

A FastAPI backend for analyzing equity portfolio sector allocation. Users can register, upload stock holdings by ISIN, and generate sector-wise allocation reports as JSON or Excel.

**Live API:** [https://portfolio-sector-allocation.onrender.com](https://portfolio-sector-allocation.onrender.com)  
**API Docs:** [https://portfolio-sector-allocation.onrender.com/docs](https://portfolio-sector-allocation.onrender.com/docs)

> **Note:** Hosted on Render's free tier. If the app hasn't received traffic recently, it may take 1–2 minutes to spin up on first load. Please allow it a moment to respond.

## Background

This project was originally built to help a financial advisor understand **sector-level exposure** across client stock portfolios — mapping individual holdings to industry/sector metadata rather than relying on surface-level labels, and generating shareable reports from that analysis.

---

## Features

- **User authentication** — JWT-based login with bcrypt password hashing
- **Holdings management** — Bulk upload, list, and delete portfolio holdings
- **ISIN validation** — Validates 12-character Indian equity ISINs against a reference instrument database
- **Sector allocation reports** — SQL-powered analytics showing sector and stock-level portfolio weights
- **Excel export** — Download allocation reports as `.xlsx` files with expiry and cleanup
- **Instrument metadata** — Pre-seeded with 4,600+ Indian equity instruments (sector, industry, symbol)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Server | Uvicorn (ASGI) |
| Database | PostgreSQL (async via SQLAlchemy + asyncpg) |
| Auth | JWT (python-jose) + OAuth2 password flow |
| Validation | Pydantic v2 |
| Reports | Pandas, OpenPyXL |
| Deployment | Render |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | No | Landing page |
| `POST` | `/login` | No | Login and receive JWT access token |
| `POST` | `/users/register` | No | Register a new user |
| `GET` | `/users/get-user-details` | Bearer | Get current user profile |
| `POST` | `/holdings/upload-holdings-json` | Bearer | Bulk upload/upsert holdings |
| `GET` | `/holdings/get-user-holdings` | Bearer | List holdings with instrument metadata |
| `DELETE` | `/holdings/delete-user-holdings` | Bearer | Delete all holdings for current user |
| `GET` | `/reports/create-allocation-report` | Bearer | Generate allocation report (`?format=json` or `?format=excel`) |
| `GET` | `/reports/download` | Bearer | Download Excel report (`?report_id=<id>` optional) |

Interactive API documentation is available at [/docs](https://portfolio-sector-allocation.onrender.com/docs) (Swagger UI) and [/redoc](https://portfolio-sector-allocation.onrender.com/redoc).

---

## Quick Start (Local)

### Prerequisites

- Python 3.10+
- PostgreSQL database
- SSL certificate file for database connection (if using a hosted provider like Supabase)

### 1. Clone the repository

```bash
git clone https://github.com/AbhishekLate8/Portfolio-sector-allocation.git
cd Portfolio-sector-allocation
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
database_username=your_db_user
database_password=your_db_password
database_hostname=your_db_host
database_port=5432
database_name=your_db_name
secret_key=your_jwt_secret_key
algorithm=HS256
access_token_expire_minutes=30
API_KEY=your_api_key
API_SECRET=your_api_secret
REDIRECT_URI=your_redirect_uri
SSL_CERT_PATH=path/to/ssl/cert.pem
```

> Do not commit `.env` to version control.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

On first startup, the app will:
- Create database tables
- Seed instrument metadata from `data/Equity.csv` (if the table is empty)
- Start a background task to clean up expired report files

---

## Example Usage

### Register

```bash
curl -X POST "http://127.0.0.1:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

### Login

```bash
curl -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

### Upload holdings

```bash
curl -X POST "http://127.0.0.1:8000/holdings/upload-holdings-json" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '[
    {"isin_no": "INE117A01022", "quantity": 10, "avg_price": 5200.50},
    {"isin_no": "INE208C01025", "quantity": 25, "avg_price": 780.00}
  ]'
```

### Get allocation report (JSON)

```bash
curl -X GET "http://127.0.0.1:8000/reports/create-allocation-report?format=json" \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Deployment (Render)

This project is deployed on [Render](https://render.com).

**Suggested Render settings:**

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Environment | Add all variables from the `.env` section above |

**Notes for Render:**
- Set environment variables in the Render dashboard (do not rely on a local `.env` file)
- Ensure `SSL_CERT_PATH` points to a valid certificate file included in the deployment or mounted via Render
- The `reports/` directory is used for temporary Excel file storage on the instance

---

## Project Structure

```
Portfolio-sector-allocation/
├── app/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Environment configuration
│   ├── database.py             # Async SQLAlchemy engine and session
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── oauth2.py               # JWT authentication
│   ├── utils.py                # Password hashing utilities
│   ├── routers/
│   │   ├── auth.py             # Login endpoint
│   │   ├── user.py             # User registration and profile
│   │   ├── holdings.py         # Holdings CRUD
│   │   └── reports.py          # Allocation reports
│   ├── services/
│   │   └── set_instruments_metadata.py  # Instrument seeding from CSV
│   └── tasks/
│       └── cleanup.py          # Expired report cleanup task
├── data/
│   └── Equity.csv              # Indian equity instrument reference data
├── static/
│   └── landing.html            # Landing page
├── requirements.txt
└── README.md
```

---

## How It Works

1. **Register / Login** — Users create an account and receive a JWT access token.
2. **Upload holdings** — Users submit a JSON array of holdings (`isin_no`, `quantity`, `avg_price`).
3. **Validation** — Each ISIN is checked against the `instruments` table; invalid ISINs are returned in the response.
4. **Generate report** — A SQL query joins holdings with instrument metadata to compute:
   - Investment per stock
   - Sector totals
   - Sector % of portfolio
   - Stock % within sector and % of portfolio
5. **Export** — Reports can be returned as JSON or saved as an Excel file for download.

---

## Database Schema

```
users (1) ──< holdings (M) >── (1) instruments
  │
  └──< reports (M)
```

| Table | Description |
|-------|-------------|
| `users` | Registered users |
| `instruments` | Equity reference data (ISIN, symbol, sector, industry) |
| `holdings` | User portfolio positions (composite key: user_id + isin_no) |
| `reports` | Generated Excel report metadata with expiry tracking |

---

## Known Limitations

This is a functional **MVP** built as an independent project, not a production deployment. Gaps that would need addressing before real-world production use:

- No automated test suite yet
- Uses SQLAlchemy's `create_all()` at startup rather than versioned migrations (e.g., Alembic)
- No rate limiting on public endpoints
- No CI/CD pipeline configured

---

## Author

**Abhishek**

- GitHub: [@AbhishekLate8](https://github.com/AbhishekLate8)
- Repository: [Portfolio-sector-allocation](https://github.com/AbhishekLate8/Portfolio-sector-allocation)
- Live Demo: [https://portfolio-sector-allocation.onrender.com](https://portfolio-sector-allocation.onrender.com)
- API Docs: [https://portfolio-sector-allocation.onrender.com/docs](https://portfolio-sector-allocation.onrender.com/docs)

---

## License

This project is for personal and portfolio use. Not licensed for commercial reuse.
