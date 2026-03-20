# FF Brain — Bot Setter Fuerza Frutal

Bot setter con IA para Fuerza Frutal. Conversa con leads por WhatsApp,
califica, entrega calendario, maneja follow-ups y extrae inteligencia.

## Setup local

1. `cp .env.example .env` y completar las keys
2. `pip install -r requirements.txt`
3. Ejecutar `scripts/setup_supabase.sql` en Supabase SQL Editor
4. `python scripts/seed_db.py` para datos iniciales
5. `uvicorn app.main:app --reload`

## Deploy (Railway)

1. Conectar repo a Railway
2. Configurar env vars en Railway dashboard
3. Deploy automático con cada push
