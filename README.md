# MucosaView - Backend (API REST)

## 🔧 Descripción
API REST desarrollada en Django para la gestión de registros médicos de pacientes gestantes. Almacena datos clínicos, fotografías de alta calidad y coordenadas GPS con soporte para múltiples visitas.

## 🚀 Repositorios del Proyecto
- **Frontend (App Móvil)**: https://github.com/JhosepSF/MucosaView-Project-Front
- **Backend (API Django)**: https://github.com/JhosepSF/MucosaView-Project-Back

## 📋 Requisitos Previos

### Software Necesario
- Python 3.13 o superior
- pip (gestor de paquetes de Python)
- MariaDB 10.4+ / MySQL 5.7+ / PostgreSQL 12+
- Virtualenv (recomendado)

### Hardware Recomendado
- **RAM**: Mínimo 2GB (recomendado 4GB+)
- **Almacenamiento**: 10GB+ (para fotos PNG)
- **Red**: Conexión estable para sincronización

## 🔧 Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/JhosepSF/MucosaView-Project-Back.git
cd MucosaView-Project-Back
```

### 2. Crear Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

**Dependencias principales**:
- Django 5.2
- djangorestframework
- django-cors-headers
- mysqlclient (para MySQL/MariaDB)
- django-storages (almacenamiento S3/MinIO)
- boto3 (AWS S3)
- pillow (procesamiento de imágenes)
- requests (geocoding)

### 4. Configurar Base de Datos

#### MariaDB/MySQL
```bash
# Crear base de datos
mysql -u root -p
CREATE DATABASE mucosa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### Configurar settings.py
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "mucosa_db",
        "USER": "root",
        "PASSWORD": "tu_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```

### 5. Aplicar Migraciones
```bash
python manage.py migrate
```

### 6. Crear Superusuario (Opcional)
```bash
python manage.py createsuperuser
```

### 7. Configurar Almacenamiento de Fotos

#### Opción 1: FileSystem Local (Desarrollo)
```python
# settings.py
USE_S3 = False

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

#### Opción 2: MinIO/S3 (Producción)
```python
# settings.py
USE_S3 = True

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_ENDPOINT_URL = "http://127.0.0.1:9000"
AWS_ACCESS_KEY_ID = "minioadmin"
AWS_SECRET_ACCESS_KEY = "minioadmin"
AWS_STORAGE_BUCKET_NAME = "mucosa-media"
```

## ▶️ Ejecución

### Modo Desarrollo
```bash
# Servidor de desarrollo Django
python manage.py runserver 0.0.0.0:8000
```

### Acceso en LAN
Para permitir conexiones desde la app móvil:
```bash
# Encuentra tu IP local
ipconfig  # Windows
ifconfig  # Linux/Mac

# Ejecuta con tu IP
python manage.py runserver 192.168.100.151:8000
```

### Modo Producción
```bash
# Con Gunicorn (Linux/Mac)
gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Con mod_wsgi (Apache)
# Ver configuración en docs/apache.conf
```

### Verificar Funcionamiento
```bash
# Health check
curl http://localhost:8000/api/diagnostics/

# Respuesta esperada
{"photos": 0, "disk_free_gb": 50.25}
```

## 📁 Estructura del Proyecto
```
Back/
├── manage.py                  # CLI de Django
├── requirements.txt          # Dependencias
├── app/                      # Configuración principal
│   ├── settings.py           # Configuraciones globales
│   ├── urls.py              # URLs principales
│   ├── wsgi.py              # WSGI para producción
│   └── asgi.py              # ASGI para async
├── core/                     # App auxiliar
│   ├── views.py             # Diagnósticos
│   └── ...
├── records/                  # App principal
│   ├── models.py            # Modelos de datos
│   │   ├── Patient          # Pacientes
│   │   ├── Visit            # Visitas
│   │   └── Photo            # Fotos
│   ├── serializers.py       # Serializadores DRF
│   ├── views.py             # Endpoints API
│   ├── signals.py           # Lógica automática
│   ├── admin.py             # Panel admin
│   ├── urls.py              # Rutas de la app
│   └── migrations/          # Migraciones de BD
│       ├── 0001_initial.py
│       ├── 0002_alter_visit_visit_number.py
│       └── 0003_alter_photo_type.py
└── media/                    # Almacenamiento de fotos
    └── photos/
        └── {DNI}/
            ├── {DNI}_Conjuntiva_1_1.png
            ├── {DNI}_Labio_1_1.png
            └── {DNI}_Indice_1_1.png
```

## 🗄️ Modelos de Datos

### Patient (Paciente)
```python
{
  "id": "uuid",
  "dni": "12345678",
  "nombre": "María",
  "apellido": "García",
  "edad": 25,
  "region": "SAN MARTIN",
  "provincia": "MOYOBAMBA",
  "distrito": "MOYOBAMBA",
  "direccion": "Jr. Lima 123",
  "maps_url": "https://www.google.com/maps?q=-6.123,-77.456",
  "created_at": "2026-01-08T10:00:00Z",
  "updated_at": "2026-01-08T10:00:00Z"
}
```

### Visit (Visita Médica)
```python
{
  "id": "uuid",
  "patient": "patient_uuid",
  "visit_number": 1,              # Auto-incrementa por paciente
  "bpm": 75,                      # Pulsaciones por minuto
  "hemoglobina": 12.5,            # g/dL
  "spo2": 98,                     # % Oxígeno
  "lmp_date": "2025-06-01",       # Fecha último periodo
  "gestational_weeks": 30,        # Calculado automáticamente
  "version": 1,                   # Optimistic locking
  "created_at": "2026-01-08T10:00:00Z"
}
```

### Photo (Fotografía Clínica)
```python
{
  "id": "uuid",
  "visit": "visit_uuid",
  "type": "CONJ",                 # CONJ | LAB | IND
  "index": 1,                     # 1 o 2
  "file": "photos/12345678/12345678_Conjuntiva_1_1.png",
  "original_name": "IMG_0001.png",
  "content_type": "image/png",
  "size": 1500000,                # bytes
  "sha256": "abc123...",          # Hash para deduplicación
  "created_at": "2026-01-08T10:00:00Z"
}
```

## 🎯 API Endpoints

### ViewSets (REST completo)

#### Pacientes
```http
GET    /api/patients/           # Lista todos
POST   /api/patients/           # Crear nuevo
GET    /api/patients/{uuid}/    # Detalle
PUT    /api/patients/{uuid}/    # Actualizar (idempotente)
PATCH  /api/patients/{uuid}/    # Actualizar parcial
DELETE /api/patients/{uuid}/    # Eliminar
```

#### Visitas
```http
GET    /api/visits/             # Lista todas
POST   /api/visits/             # Crear nueva
GET    /api/visits/{uuid}/      # Detalle + ETag
PUT    /api/visits/{uuid}/      # Actualizar (optimistic lock)
PATCH  /api/visits/{uuid}/      # Actualizar parcial
DELETE /api/visits/{uuid}/      # Eliminar
```

#### Fotos
```http
GET    /api/photos/             # Lista todas
POST   /api/photos/             # Crear nueva
GET    /api/photos/{uuid}/      # Detalle
DELETE /api/photos/{uuid}/      # Eliminar
```

### Endpoints Especializados

#### Registro Completo (Visita 1)
```http
POST /api/mucosa/registro
Content-Type: application/json

{
  "client_uuid": "uuid-v4",
  "datos_personales": {
    "dni": "12345678",
    "nombre": "María",
    "apellido": "García",
    "edad": 25,
    "region": "SAN MARTIN",
    "provincia": "MOYOBAMBA",
    "distrito": "MOYOBAMBA",
    "direccion": "Jr. Lima 123",
    "mapsUrl": "https://...",
    "lat": -6.123,
    "lng": -77.456
  },
  "datos_obstetricos": {
    "pulsaciones": "75",
    "hemoglobina": "12.5",
    "oxigeno": "98",
    "fechaUltimoPeriodo": "2025-06-01"
  },
  "nro_visita": 1
}

Response 201:
{
  "patient_id": "uuid",
  "visit_id": "uuid",
  "visit_number": 1,
  "gestational_weeks": 30
}
```

#### Subida de Fotos
```http
POST /api/mucosa/registro/{dni}/fotos
Content-Type: multipart/form-data

Body:
- file: archivo PNG
- type: CONJ | LAB | IND
- index: 1 | 2
- nro_visita: 1
- original_name: IMG_0001.png (opcional)
- content_type: image/png (opcional)

Response 201:
{
  "photo_id": "uuid",
  "visit_id": "uuid",
  "stored_as": "photos/12345678/12345678_Conjuntiva_1_1.png"
}
```

#### Visita Adicional
```http
POST /api/mucosa/registro/{dni}/visita
Content-Type: application/json

{
  "datos_obstetricos": {
    "pulsaciones": "78",
    "hemoglobina": "13.0",
    "oxigeno": "99",
    "fechaUltimoPeriodo": "2025-06-01"
  },
  "nro_visita": 2
}

Response 201:
{
  "patient_id": "uuid",
  "visit_id": "uuid",
  "visit_number": 2,
  "gestational_weeks": 32
}
```

#### Deduplicación por Hash
```http
HEAD /api/media/by-hash/{sha256}

Response 200: Foto ya existe
Response 404: Foto no existe
```

#### Diagnósticos
```http
GET /api/diagnostics/

Response 200:
{
  "photos": 150,
  "disk_free_gb": 45.5
}
```

## 🔄 Características Especiales

### 1. Upsert Idempotente
Los endpoints `PUT` crean el recurso si no existe:
```python
# Si el recurso no existe, lo crea
PUT /api/patients/{uuid}/  → 201 Created

# Si existe, lo actualiza
PUT /api/patients/{uuid}/  → 200 OK
```

### 2. Optimistic Locking (Visitas)
Previene conflictos de escritura concurrente:
```http
GET /api/visits/{uuid}/
ETag: "v1"

PUT /api/visits/{uuid}/
If-Match: "v1"
→ 200 OK, ETag: "v2"

PUT /api/visits/{uuid}/
If-Match: "v1"  # (versión desactualizada)
→ 412 Precondition Failed
```

### 3. Auto-Numeración de Visitas
El campo `visit_number` se asigna automáticamente:
```python
# Visita 1 del paciente → visit_number = 1
# Visita 2 del paciente → visit_number = 2
# etc.
```

### 4. Geocoding Automático (Reverse)
Si el frontend envía coordenadas GPS pero faltan datos de ubicación, el backend completa automáticamente usando Nominatim (OpenStreetMap):
```python
lat=-6.123, lng=-77.456
    ↓
Nominatim Reverse Geocoding
    ↓
region="San Martín", provincia="Moyobamba", ...
```

### 5. Deduplicación de Fotos
Usa SHA-256 para detectar fotos duplicadas:
```python
HEAD /api/media/by-hash/{sha256}
→ 200: No subir (ya existe)
→ 404: Subir foto
```

### 6. Constraint de Unicidad
Previene fotos duplicadas:
```sql
UNIQUE(visit, type, index)
```
Ejemplo: Solo puede haber 1 foto de tipo "CONJ" con index=1 por visita.

## 🛠️ Tecnologías Utilizadas

### Framework y API
- **Django 5.2**: Framework web
- **Django REST Framework**: API REST
- **django-cors-headers**: CORS para frontend

### Base de Datos
- **mysqlclient 2.2.7**: Adaptador MySQL/MariaDB
- **PostgreSQL** (alternativa soportada)
- **SQLite** (desarrollo)

### Almacenamiento
- **django-storages**: Backend S3/MinIO
- **boto3**: Cliente AWS S3
- **Pillow**: Procesamiento de imágenes

### Utilidades
- **requests**: Geocoding con Nominatim
- **hashlib**: Cálculo de SHA-256

## ⚙️ Configuración Avanzada

### MariaDB 10.4 (Workaround)
Django 5.2 requiere MariaDB 10.5+, pero el código incluye un parche:
```python
# settings.py (línea 60)
def check_database_version_supported_patch(self):
    pass

base.BaseDatabaseWrapper.check_database_version_supported = check_database_version_supported_patch  # type: ignore
```

### CORS (Cross-Origin)
```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Solo desarrollo

# Producción
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio.com",
]
```

### Logging
```python
# settings.py
LOGGING = {
    "loggers": {
        "records": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
```

### Almacenamiento S3/MinIO
```python
# settings.py
USE_S3 = True
AWS_S3_ENDPOINT_URL = "http://127.0.0.1:9000"
AWS_ACCESS_KEY_ID = "minioadmin"
AWS_SECRET_ACCESS_KEY = "minioadmin"
AWS_STORAGE_BUCKET_NAME = "mucosa-media"
```

## 🐛 Solución de Problemas

### Error: "No module named 'mysqlclient'"
```bash
# Windows
pip install mysqlclient

# Si falla, instalar desde wheel:
pip install https://download.lfd.uci.edu/pythonlibs/archived/mysqlclient-2.2.7-cp313-cp313-win_amd64.whl
```

### Error: MariaDB version incompatible
El código ya incluye el parche en `settings.py`. Verifica que esté presente.

### Error: "RETURNING not supported"
MariaDB 10.4 no soporta `RETURNING`. Usa el script manual:
```bash
python migrate_indice.py
```

### Fotos no se guardan
1. Verifica permisos de escritura en `media/`
2. Comprueba espacio en disco
3. Revisa logs: `python manage.py runserver --verbosity 2`

### Geocoding no funciona
1. Verifica conexión a internet del servidor
2. Comprueba logs: `logger.warning` en `views.py`
3. Nominatim puede tener rate limiting

## 📊 Panel de Administración

Accede al admin de Django:
```
http://localhost:8000/admin/

# Login con superusuario creado
```

**Modelos disponibles**:
- ✅ Patients
- ✅ Visits
- ✅ Photos

**Filtros y búsqueda**:
- Buscar por DNI, nombre, apellido
- Filtrar visitas por paciente
- Buscar fotos por SHA-256

## 📈 Rendimiento

### Métricas
- **Registro completo**: ~500ms
- **Subida de foto**: ~200ms (1.5MB PNG)
- **Geocoding**: ~800ms (si se activa)
- **Capacidad**: 1000+ pacientes simultáneos

### Optimizaciones
- Índices en `dni`, `sha256`
- Select related en queries
- Transacciones atómicas
- Validación temprana

## 🔐 Seguridad

### Implementado
- ✅ Validación de entrada (serializadores DRF)
- ✅ Transacciones atómicas
- ✅ CORS configurado
- ✅ SQL injection protection (ORM)
- ✅ Idempotencia con UUIDs

## 🧪 Testing
```bash
# Ejecutar tests
python manage.py test records

# Con coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Despliegue

### Docker
```dockerfile
FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Nginx (Reverse Proxy)
```nginx
server {
    listen 80;
    server_name api.mucosaview.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /media/ {
        alias /var/www/mucosaview/media/;
    }
}
```

## 🔄 Migraciones

### Crear nueva migración
```bash
python manage.py makemigrations records
```

### Aplicar migraciones
```bash
python manage.py migrate
```

### Historial
```bash
python manage.py showmigrations
```

## 👥 Autor
JhosepSF

## 📄 Licencia
Este proyecto es parte de un trabajo académico.

## 📞 Soporte
Para más información:
- **Frontend README**: [App Móvil](https://github.com/JhosepSF/MucosaView-Project-Front)
- **Issues**: Reportar en GitHub Issues

## 🔄 Versiones
- **v1.0.0** - API REST completa con soporte offline-first
  - Endpoints especializados para app móvil
  - Geocoding automático
  - Optimistic locking
  - Deduplicación de fotos
  - Soporte para 3 tipos de fotos (Conjuntiva, Labio, Índice)
