# 🎬 Cine Paradiso - Sistema de Venta de Entradas de Cine

**Materia:** Introducción al Desarrollo de Software (FIUBA - Cátedra Lanzillotta, 2.º Cuatrimestre 2026)  
**Proyecto:** Sistema Web de Cartelera, Venta de Entradas y Backoffice Administrativo

---

## 🏛️ Arquitectura y Cumplimiento de Pautas de la Cátedra

1. **Separación Backend y Frontend en Flask:**
   * **Backend (`backend/`):** API REST pura en Flask (puerto 5000) que expone endpoints JSON con verbos HTTP adecuados (`GET`, `POST`, `PATCH`, `DELETE`).
   * **Frontend (`frontend/`):** Servidor web en Flask (puerto 5001) con templates Jinja2 y CSS responsive. Consume la API del backend desde Python mediante la librería `requests`.
2. **Cero ORM (Sin SQLAlchemy ni mapeos automáticos):** Todas las consultas e inserciones a MySQL se realizan mediante sentencias SQL explícitas y parametrizadas (`%s`), previniendo inyección SQL.
3. **Cero peticiones desde el navegador:** No se utilizan `fetch`, `axios`, `promises` ni llamadas AJAX desde el cliente; toda la comunicación la resuelve el servidor Flask del front.
4. **Fechas y Horarios:** Se utiliza un único campo `DATETIME` para fecha y hora de funciones.
5. **Seguridad y Roles:** Endpoints protegidos con tokens de autenticación Bearer (`administrador` y `cliente`).
6. **Entradas y QR 100% Offline:** Códigos QR generados localmente con token aleatorio único de un solo uso por compra, con control de superposiciones y 20 minutos de limpieza entre funciones.
7. **Backoffice de Administrador:** Módulo con panel de métricas y estadísticas, ABM de servicios y validación de QR en puerta (Hito 3).
8. **Pruebas Automatizadas:** Batería de tests con `pytest` que verifica el cumplimiento de las reglas de negocio.

---

## 📂 Estructura del Repositorio

```text
cine-paradiso/
├── docker-compose.yml        # Orquestación con Docker (MySQL + Backend + Frontend)
├── .env.example              # Variables de entorno de configuración
├── .gitignore                # Reglas de exclusión de Git
├── README.md                 # Documentación del proyecto
├── init.sh                   # Script de instalación automática de dependencias
├── requirements.txt          # Dependencias de Python (Flask, PyMySQL, requests, qrcode, pytest, reportlab)
│
├── sql/
│   └── init_db.sql           # Creación de tablas, constraints, triggers y seed data
│
├── tests/
│   └── test_reglas_negocio.py # Pruebas unitarias automatizadas con pytest
│
├── backend/                  # API REST en Flask (Puerto 5000)
│   ├── Dockerfile            # Imagen Docker del Backend
│   ├── app.py                # Entrada principal de la API
│   └── src/
│       ├── config.py         # Configuración del Backend
│       ├── db.py             # Conexión pura con PyMySQL y context managers
│       ├── errors.py         # Manejo centralizado de excepciones y errores JSON
│       ├── http_utils.py     # Helpers de serialización JSON y formateo
│       ├── security.py       # Hasheo de contraseñas y tokens Bearer
│       ├── qr_utils.py       # Generador de códigos QR binarios en Python
│       ├── repos/            # Consultas SQL explícitas (usuarios, películas, compras, estadísticas, etc.)
│       └── routes/           # Blueprints de endpoints (auth, películas, compras, admin, etc.)
│
└── frontend/                 # Servidor Web en Flask (Puerto 5001)
    ├── Dockerfile            # Imagen Docker del Frontend
    ├── app.py                # Entrada principal del Frontend
    ├── src/
    │   ├── config.py         # Configuración del Frontend
    │   ├── api_client.py     # Cliente HTTP requests hacia la API REST
    │   ├── qr_utils.py       # Generador de QR offline en Base64 para Jinja2
    │   └── routes/           # Rutas públicas, de cliente y de administración
    ├── static/               # Hojas de estilo responsive
    │   └── css/base.css
    └── templates/            # Plantillas Jinja2
        ├── base.html
        ├── components/       # navbar.html, footer.html
        ├── public/           # index.html, pelicula.html, butacas.html
        ├── cliente/          # comprobante.html, perfil.html
        ├── auth/             # login.html, registro.html
        └── admin/            # dashboard.html, validar_qr.html, servicios.html
```

---

## 🚀 Puesta en Marcha

### Opción A: Con Docker (Recomendada y automatizada)
Si tenés Docker instalado, levantá todo el sistema con un solo comando:
```bash
docker compose up --build
```
* La base de datos MySQL 8 se iniciará y precargará las tablas automáticamente.
* El Backend estará disponible en `http://localhost:5000`.
* El Frontend estará disponible en `http://localhost:5001`.

---

### Opción B: Ejecución Local Manual

1. **Base de Datos:**
   Crear la base de datos y cargar el esquema inicial ejecutando:
   ```bash
   mysql -u root -p < sql/init_db.sql
   ```

2. **Instalación de dependencias:**
   En Linux/macOS/Git Bash:
   ```bash
   chmod +x init.sh
   ./init.sh
   ```
   O en Windows PowerShell:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Ejecución:**
   * Iniciar el Backend (puerto 5000):
     ```bash
     python backend/app.py
     ```
   * En otra terminal, iniciar el Frontend (puerto 5001):
     ```bash
     python frontend/app.py
     ```
   * Abrir el navegador en: **`http://localhost:5001`**

---

## 🧪 Ejecución de Pruebas Automatizadas

Para validar las reglas de negocio (máximo de 6 entradas, cancelaciones hasta 2hs antes, contraseñas seguras y generación de QR offline):
```bash
pytest tests/ -v
```
