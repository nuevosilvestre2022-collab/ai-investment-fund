# 🏦 AI Investment Fund

> **Filosofía híbrida:** Margen de Seguridad de Buffett × 10-Baggers de Lynch

Sistema multi-agente con CrewAI que analiza 6 regiones del mundo y genera un portfolio de inversión inteligente.

---

## 🚀 Setup (5 minutos)

### 1. Entorno virtual
```bash
cd "c:\Users\ssilv\Desktop\IA\Antigravity\Fondo de Invesion IA\fondo_ia"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Keys (costo cero para empezar)

Copiar `.env.example` → `.env` y completar:

| Variable | Dónde obtenerla | Costo |
|---|---|---|
| `GOOGLE_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | **GRATIS** (15 RPM, 1M tokens/día) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Pay-per-use (~$0.50-2/semana) |

```bash
copy .env.example .env
# Editar .env con tus keys
```

---

## 📟 Uso

### Analizar una sola acción (sin LLM, 100% gratis)
```bash
python main.py --mode valuation --ticker AAPL
python main.py --mode valuation --ticker VALE3.SA MSFT TSM
```

### Test rápido del sistema
```bash
python main.py --mode test
```

### Análisis completo de una región
```bash
python main.py --mode full --region north_america
python main.py --mode full --region latam
python main.py --mode full --region asia
```

### Análisis global completo (todas las regiones)
```bash
python main.py
```

### Dashboard visual
```bash
python dashboard/app.py
# Abrir http://localhost:5000
```

---

## 🌍 Regiones cubiertas

| Región | Mercados | Riesgo |
|---|---|---|
| `north_america` | NYSE, NASDAQ, TSX, BMV | Bajo |
| `europe_north` | LSE, XETRA, OMX | Bajo |
| `europe_south` | IBEX, MIB, PSI | Medio |
| `asia` | TSE, NSE, TSM, KOSPI | Medio |
| `latam` | BOVESPA, MERVAL, BCS | Alto |
| `africa` | JSE, NGX | Alto |

---

## 🤖 Agentes

| Agente | Inspiración | Función |
|---|---|---|
| Market Scout | Peter Lynch | Encuentra oportunidades no descubiertas |
| Fundamental Analyst | Warren Buffett | Moat, ROE, FCF, intrinsic value |
| Growth Hunter | Peter Lynch | Caza 10-baggers con PEG < 1.5 |
| Risk Evaluator | Benjamin Graham | Margen de seguridad ≥ 30% |
| Macro Analyst | George Soros | Contexto macro/geopolítico por región |
| Portfolio Manager | Híbrido | Sintetiza el portfolio final |

---

## 💰 Costo estimado de uso

- Análisis semanal completo (6 regiones): **~$0.50 – $2.00 USD**
- Valuación individual de acciones: **$0.00** (solo yfinance)
- Dashboard: **$0.00**
