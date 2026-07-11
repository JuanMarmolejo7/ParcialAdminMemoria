# Simulador de asignacion contigua (consola). Solo usa la libreria estandar.
FROM python:3.12-slim

WORKDIR /app
COPY . .

# Salida sin buffer para que los menus se vean de inmediato.
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "cli.py"]