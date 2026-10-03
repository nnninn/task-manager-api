# Task Manager API

![Tests](https://github.com/USERNAME/task-manager-api/actions/workflows/tests.yml/badge.svg)

REST API untuk mengurus task peribadi, dibina dengan FastAPI. Setiap user
mempunyai akaun sendiri dan hanya boleh melihat serta mengurus task miliknya.

## Ciri-ciri

- Register dan login dengan password yang di-hash (Argon2)
- Pengesahan menggunakan JWT token
- CRUD penuh untuk task (create, read, update, delete)
- Setiap user hanya boleh akses task sendiri
- Dokumentasi API automatik (Swagger UI)
- Validation data dengan Pydantic
- Test automatik dengan pytest, dijalankan melalui GitHub Actions

## Tech Stack

Python, FastAPI, SQLAlchemy, SQLite, PyJWT, Pydantic, pytest, GitHub Actions

## Cara Run

1. Clone repo:

```
   git clone https://github.com/USERNAME/task-manager-api.git
   cd task-manager-api
```

2. Cipta virtual environment dan install library:

```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
```

   (Pada Mac/Linux, guna `source venv/bin/activate`.)

3. Cipta fail `.env` daripada templat, dan jana `SECRET_KEY`:

```
   copy .env.example .env
   python -c "import secrets; print(secrets.token_hex(32))"
```

   Salin kunci yang dijana dan letak dalam `.env` sebagai nilai `SECRET_KEY`.

4. Jalankan server:

```
   uvicorn main:app --reload
```

5. Buka dokumentasi di `http://127.0.0.1:8000/docs`

## Menjalankan Test

```
pytest
```

Test menggunakan database dalam memori, jadi data sebenar tidak terjejas.

## Endpoint

| Method | Endpoint | Penerangan | Perlu login |
|--------|----------|------------|-------------|
| POST | /register | Daftar akaun baru | Tidak |
| POST | /login | Login dan dapatkan token | Tidak |
| POST | /tasks | Tambah task | Ya |
| GET | /tasks | Senarai task sendiri | Ya |
| GET | /tasks/{id} | Lihat satu task | Ya |
| PUT | /tasks/{id} |