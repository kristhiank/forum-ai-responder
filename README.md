# 1031 Exchange Forum Monitor — POC

Sistema automatizado que monitorea Reddit en busca de menciones de "1031 exchange",
genera respuestas con Claude, solicita aprobación por email y publica automáticamente.

## Flujo completo

```
Reddit → scraper.py → responder.py (Claude) → emailer.py → [APROBA/RECHAZA]
                                                                    ↓
                                                           approval_server.py
                                                                    ↓
                                                             poster.py → Reddit
```

## Setup rápido

### 1. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configurar credenciales
```bash
copy .env.example .env
# Editar .env con tus credenciales
```

Credenciales necesarias:
| Servicio | Dónde obtenerlo |
|----------|----------------|
| Reddit API | https://www.reddit.com/prefs/apps (tipo: script) |
| Claude API | https://console.anthropic.com/ |
| Gmail App Password | https://myaccount.google.com/apppasswords |

### 3. Ejecutar
```bash
python main.py
```

El sistema arranca dos procesos en paralelo:
- **Monitor loop** — escanea Reddit cada 5 minutos
- **Approval server** — escucha en http://localhost:5055

### Dashboard
Abre http://localhost:5055/status para ver todos los posts procesados.

## Archivos

| Archivo | Función |
|---------|---------|
| `config.py` | Centraliza toda la configuración |
| `database.py` | SQLite: tracking de posts y estado |
| `scraper.py` | PRAW — busca keyword matches en Reddit |
| `responder.py` | Claude API — genera borradores de respuesta |
| `emailer.py` | Gmail SMTP — envía email de aprobación con botones |
| `approval_server.py` | Flask — recibe clicks de Aprobar/Rechazar |
| `poster.py` | PRAW — publica el reply aprobado en Reddit |
| `main.py` | Orquesta todo en un loop continuo |

## Estados de un post

```
pending → draft_ready → pending_approval → approved → posted
                                         ↘ rejected
                   (error en cualquier punto) → error
```
