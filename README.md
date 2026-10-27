# Sistema de Evaluación IC

Aplicación web para registrar, consultar y analizar evaluaciones de desempeño de analistas de Inteligencia Comercial (IC). 
Desarrollada con **Python, Flask y SQL Server**, reúne formularios por rol, dashboards históricos, análisis gerencial con **Ollama** y 
notificaciones por correo electrónico.

> **Proyecto personal de aprendizaje.**
> Este repositorio es un ejercicio independiente para practicar desarrollo web, bases de datos, automatización y modelos de lenguaje locales.
> No fue desarrollado como parte de una relación laboral anterior y no representa un producto oficial de ninguna empresa u organización.

## Funcionamiento
El administrador registra analistas, canales y usuarios autorizados. Los evaluadores acceden al formulario que corresponde a su rol y registran las 
respuestas del periodo seleccionado. Las evaluaciones interna y del cliente se guardan por separado; no es necesario completarlas simultáneamente.
El sistema calcula los resultados, los presenta en un dashboard y conserva un historial consultable. Desde el panel también es posible solicitar un 
análisis gerencial generado por Ollama. Cuando una evaluación está completa y su resultado es inferior al umbral configurado en el código, el 
administrador puede procesar alertas dirigidas a los coordinadores del canal correspondiente.

### Roles y módulos

| Rol | Acceso principal |
| Administrador | Gestión de analistas, canales, evaluadores, accesos, reportes, carga de Excel y alertas. |
| Controller | Formulario de evaluación interna. |
| Cliente | Formulario de evaluación del cliente. |
| Coordinador | Consulta del dashboard correspondiente a su canal. |

El acceso actual se basa en el correo registrado y el rol asociado. 
**No sustituye a un mecanismo de autenticación con verificación de identidad**; se debe reforzar antes de exponer la aplicación públicamente.

### Evaluaciones y puntajes
| Evaluación | Preguntas | Puntaje máximo |
| Interna | 9 | 45 |
| Cliente | 5 | 55 |
| **Total** | **14** | **100** |

Las preguntas se responden en una escala del 1 al 5 y tienen ponderaciones distintas. Los ítems relacionados con inconsistencias aplican una puntuación inversa.
Mientras falta una de las dos evaluaciones, el cálculo utiliza **provisionalmente el 90 % del puntaje máximo** del componente pendiente. 
Por ello, la nota mostrada antes de completar ambas encuestas **no es definitiva**. 
El sistema distingue los registros sin evaluar, con evaluación parcial y con evaluación completa.
La clasificación de resultados considera los siguientes rangos para registros evaluados:

| Puntaje | Estado |
| 90 a 100 | Excelente |
| 75 a menos de 90 | Cumple |
| 60 a menos de 75 | En desarrollo |
| Menos de 60 | Requiere mejora |

### Dashboards e historial

El panel reúne indicadores del periodo, resultados individuales, agregados por canal y seguimiento histórico. También permite consultar 
respuestas de encuestas anteriores. Los coordinadores tienen una vista limitada a su canal.

### Análisis gerencial con Ollama
La integración de IA está implementada en `ia.py`. Al solicitar un análisis desde el dashboard, Flask prepara un conjunto de datos del periodo y 
consulta la API local de Ollama (`/api/chat`). El modelo predeterminado es **`gemma3:4b`**.

La respuesta se organiza en cuatro apartados:
- Resumen ejecutivo.
- Canales prioritarios.
- Acciones recomendadas.
- Datos pendientes.

**Ollama no modifica las evaluaciones ni recalcula los puntajes.** El cálculo se realiza en `calculos.py`; el modelo recibe los resultados para redactar 
una interpretación gerencial. El análisis se genera bajo demanda y requiere que Ollama esté disponible desde el equipo o servidor que ejecuta Flask.

### Correos y alertas
El módulo `alertas_email.py` permite procesar alertas de bajo desempeño. Para una evaluación completa con puntaje **inferior a 75**, 
el sistema registra una alerta y agrupa los casos por coordinador y canal. Los mensajes se envían en formato HTML y se guarda un control 
de entregas para evitar reenviar la misma alerta al mismo coordinador.

El envío admite **SMTP** o **Outlook de escritorio** (este último requiere Windows, Outlook y `pywin32`). 
La funcionalidad es de envío a múltiples destinatarios según los coordinadores registrados; no es una plataforma de campañas de marketing.

### Gestión de información en Excel
El administrador puede importar información de reportes y analistas desde archivos Excel. El repositorio también incluye una ruta para obtener 
una plantilla de reportes. Las importaciones realizan validaciones antes de registrar la información.

## Tecnologías
| Componente | Tecnología |
| Backend | Python, Flask |
| Base de datos | Microsoft SQL Server, SQLAlchemy, pyodbc |
| Frontend | HTML, CSS, JavaScript |
| Inteligencia artificial | Ollama, API HTTP local |
| Archivos Excel | openpyxl |
| Correos | SMTP / Outlook de escritorio |
| Servidor WSGI | Waitress |

## Estructura del proyecto
```text
app.py                 # Rutas, formularios, dashboard y administración
config.py              # Configuración de SQL Server
models.py              # Modelos de base de datos
calculos.py            # Ponderaciones, puntajes y estados
ia.py                  # Análisis gerencial con Ollama
alertas_email.py       # Correos y alertas por canal
inicializar_bd.py      # Inicialización de la base de datos
requirements.txt       # Dependencias Python
templates/              # Vistas HTML
static/                 # Estilos y JavaScript
*.sql                   # Scripts de actualización y migración
```

## Instalación local

### Requisitos

- Python compatible con las dependencias del proyecto.
- Microsoft SQL Server accesible desde el equipo.
- ODBC Driver 17 o 18 para SQL Server.
- Ollama instalado y ejecutándose, **solo si se desea utilizar el análisis con IA**.
- Configuración SMTP u Outlook, **solo si se desea enviar correos**.

### 1. Preparar el entorno

Clona el repositorio y entra en su carpeta. En Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configurar SQL Server

Crea un archivo `.env` en la raíz del proyecto:

```dotenv
SECRET_KEY=reemplazar-por-una-clave-aleatoria-segura
SQLSERVER_HOST=NOMBRE_DE_TU_SERVIDOR
SQLSERVER_DATABASE=EvaluacionIC
SQLSERVER_DRIVER=ODBC Driver 17 for SQL Server
SQLSERVER_TRUST_CERTIFICATE=yes
```

La configuración incluida utiliza **autenticación integrada de Windows** (`Trusted_Connection=yes`). 
Si tu entorno utiliza otro método de autenticación, puedes proporcionar una URL de conexión mediante `DATABASE_URL`.

**Nota:** `config.py` contiene un nombre de servidor local como valor predeterminado. Configura `SQLSERVER_HOST` para tu equipo; 
antes de publicar el código conviene reemplazar ese valor por uno genérico.

### 3. Crear tablas e iniciar Flask
```powershell
flask --app app crear-tablas
flask --app app run
```

Abre `http://127.0.0.1:5000` en el navegador. Para ingresar necesitarás un correo autorizado en la base de datos.

### 4. Activar el análisis con Ollama (opcional)

Instala Ollama y descarga el modelo utilizado por defecto:

```powershell
ollama pull gemma3:4b
```

Asegúrate de que el servicio esté en ejecución. Si necesitas cambiar la dirección o el modelo, configura:

```dotenv
OLLAMA_MODEL=gemma3:4b
OLLAMA_URL=http://127.0.0.1:11434/api/chat
```

La IA solo se utiliza cuando se solicita el análisis desde el dashboard.

### 5. Configurar correos (opcional)

Para SMTP, agrega al `.env` los datos de tu proveedor:

```dotenv
MAIL_BACKEND=smtp
SMTP_HOST=servidor.smtp.ejemplo
SMTP_PORT=587
SMTP_FROM=remitente@ejemplo.com
SMTP_USER=usuario@ejemplo.com
SMTP_PASSWORD=contraseña_o_clave_de_aplicacion
SMTP_SSL=false
```

El proyecto usa STARTTLS cuando `SMTP_SSL=false`. No incluyas credenciales reales en el repositorio.

Para utilizar Outlook de escritorio, configura `MAIL_BACKEND=outlook` e instala `pywin32` en un entorno Windows compatible.

Puedes comprobar el envío con una dirección propia:

```powershell
flask --app app probar-correo --destino tu-correo@ejemplo.com
```

Para procesar las alertas del periodo, el proyecto también incluye el comando `flask --app app enviar-alertas`. 
Revisa primero sus opciones y la configuración de destinatarios; este comando puede enviar correos reales.

## Scripts SQL

El repositorio incluye `ACTUALIZACION_PREGUNTAS_SQLSERVER.sql` y `MIGRACION_LIMPIEZA_SQLSERVER.sql`. 
Estos scripts están destinados a ajustes de estructura o datos. **Revísalos y realiza una copia de seguridad antes de ejecutarlos sobre una base existente.**

## Alcance y limitaciones
Este proyecto es una implementación educativa y no debe considerarse listo para producción sin una revisión adicional de seguridad, autenticación, autorización, 
configuración y pruebas. En particular, el acceso basado únicamente en correo registrado necesita un mecanismo de verificación de identidad. El análisis con 
IA depende de un servicio Ollama accesible y sus resultados deben revisarse antes de utilizarse para tomar decisiones.
Los nombres, formularios y escenarios que aparezcan en el proyecto se utilizan con fines de demostración y no implican vinculación institucional. 
No se deben publicar datos reales de personas, evaluaciones, contraseñas ni información confidencial.

## Autoría y finalidad
Desarrollé este sistema por iniciativa propia para profundizar en la construcción de aplicaciones web, el modelado de datos, la automatización de notificaciones 
y la integración de modelos de lenguaje ejecutados localmente. Es un proyecto personal de aprendizaje, independiente de cualquier trabajo anterior.
