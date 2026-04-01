# Registro laboral (Flask + CSV)

Aplicacion Flask de una sola pantalla para fichar entrada/salida.

## Caracteristicas

- Mobile-first
- Dos botones grandes: Enter y Leave
- Listado de sesiones agrupado por semana
- Total de horas por semana
- Sin autenticacion
- Persistencia en CSV
- Docker listo para despliegue

## Estructura de datos (CSV)

Archivo en `CSV_PATH` (por defecto `/data/sessions.csv` en Docker):

- `id`
- `start_at` (ISO datetime en UTC)
- `end_at` (ISO datetime en UTC, vacio si sesion abierta)
- `created_at` (ISO datetime en UTC)

## Ejecucion local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir: http://localhost:5000

## Ejecucion con Docker

```bash
docker compose up --build
```

La persistencia queda en `./data/sessions.csv` del host gracias al volumen `./data:/data`, por lo que no se borra al parar el contenedor.

## Variables de entorno

- `TZ` (default `Europe/Madrid`)
- `CSV_PATH` (default `/data/sessions.csv` en Docker)
- `SECRET_KEY`

Puedes copiar `.env.example` a `.env` si lo necesitas.
