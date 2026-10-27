## Sobre el proyecto

Este proyecto fue desarrollado por iniciativa propia con fines educativos y de aprendizaje, como parte de mi interés por fortalecer mis conocimientos en desarrollo web, bases de datos y automatización de procesos.
Su desarrollo me permitió poner en práctica tecnologías como Python, Flask y SQL Server, así como explorar la implementación de formularios, sistemas de evaluación y visualización de información.
Es un proyecto personal e independiente, no corresponde a un desarrollo realizado durante una relación laboral anterior ni representa un sistema oficial de ninguna empresa u organización.

## Funcionalidades

- Formularios independientes para la evaluación interna y la evaluación del cliente.
- Acceso por correo corporativo y permisos según el rol registrado.
- Gestión de analistas, usuarios y canales comerciales.
- Cálculo de resultados sobre 100 puntos: 45 de evaluación interna y 55 de evaluación del cliente.
- Consulta de evaluaciones pendientes, resultados por canal e historial.
- Alertas de bajo desempeño cuando se completan ambas evaluaciones y el resultado es inferior a 75 puntos.

## Tecnologías

- Python y Flask
- SQLAlchemy y Microsoft SQL Server
- HTML, CSS y JavaScript
- pyodbc para la conexión a SQL Server

## Instalación local

Se requiere Python, una instancia accesible de SQL Server y el controlador ODBC correspondiente.

1. Clonar el repositorio e ingresar a la carpeta del proyecto.
2. Crear un entorno virtual e instalar las dependencias:

   ```bash
   python -m venv .venv
   ```

   En Windows (PowerShell):

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Crear un archivo `.env` en la raíz del proyecto y definir la conexión:

   ```dotenv
   SECRET_KEY=cambiar-por-una-clave-segura
   SQLSERVER_HOST=SERVIDOR_SQL
   SQLSERVER_DATABASE=EvaluacionIC
   SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
   SQLSERVER_TRUST_CERTIFICATE=yes
   ```

   La configuración actual utiliza autenticación integrada de Windows (`Trusted_Connection=yes`). También admite una URL de conexión completa mediante `DATABASE_URL`.

4. Inicializar las tablas y ejecutar la aplicación:

   ```bash
   flask --app app crear-tablas
   flask --app app run
   ```

La aplicación se abre en `http://localhost:5000`.

## Evaluaciones y resultados

La evaluación interna contiene nueve preguntas calificables y aporta hasta 45 puntos. La evaluación del cliente contiene cinco preguntas calificables y un campo de comentarios, con un máximo de 55 puntos. Algunas preguntas sobre inconsistencias utilizan puntuación inversa.

Los formularios pueden registrarse por separado. Mientras falte una evaluación, el sistema utiliza una puntuación temporal para el componente pendiente; ese valor no debe interpretarse como una evaluación definitiva.

## Base de datos

El repositorio incluye `ACTUALIZACION_PREGUNTAS_SQLSERVER.sql` y `MIGRACION_LIMPIEZA_SQLSERVER.sql` para tareas de actualización de la estructura. Antes de ejecutar scripts sobre una base con información existente, realiza una copia de seguridad y revisa las operaciones que contienen.

## Consideraciones de despliegue

El servidor de desarrollo de Flask es solo para uso local. Para publicar la aplicación, configura un servidor de aplicaciones, una base de datos accesible y las variables de entorno necesarias. Evita subir archivos `.env`, credenciales o datos reales de evaluaciones al repositorio.
