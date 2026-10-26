"""
Signal Lab Pro — AI Conclusion Engine
=======================================
Multi-LLM provider with instant failover:
  Primary:  Google Gemini API (gemini-flash-latest / gemini-3.8-flash)
  Fallback: Groq API (console.groq.com - Free Llama-3.3 70B / Llama-3.1 8B)
  Optional: xAI Grok (console.x.ai)

Designed for speed and reliability:
- Direct HTTP requests to avoid heavy SDK retry loops.
- If Gemini returns 503 / 429 / timeout (due to demand spikes),
  it instantly fails over to Groq within 1 second.
"""

import os
import logging
import requests

logger = logging.getLogger("ai_engine")

# ── Primary: Gemini ──────────────────────────────────────────────────────────
GEMINI_MODELS = ["gemini-flash-latest", "gemini-3.8-flash"]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# ── Fallback 1: Groq (Free tier at console.groq.com) ─────────────────────────
GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Fallback 2: xAI Grok (console.x.ai) ──────────────────────────────────────
XAI_MODELS = ["grok-2-latest", "grok-2"]
XAI_API_URL = "https://api.x.ai/v1/chat/completions"


def get_keys():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key   = os.environ.get("GROQ_API_KEY", "").strip()
    grok_key   = (
        os.environ.get("XAI_API_KEY", "").strip()
        or os.environ.get("GROK_API_KEY", "").strip()
    )
    return gemini_key, groq_key, grok_key


def call_gemini(prompt: str, api_key: str) -> dict:
    """Fast REST call to Gemini with immediate failover on 503/429/timeout."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 400},
    }

    last_error = None
    for model in GEMINI_MODELS:
        url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return {
                            "text": parts[0]["text"].strip(),
                            "provider": "Gemini",
                            "model": model,
                        }
            if resp.status_code in (503, 429):
                logger.warning(f"[AI Engine] Gemini {model} returned {resp.status_code}. Triggering fallback.")
                raise RuntimeError(f"Gemini {resp.status_code} (High Demand)")
            else:
                last_error = RuntimeError(f"Gemini error {resp.status_code}: {resp.text[:150]}")
        except requests.exceptions.Timeout:
            logger.warning(f"[AI Engine] Gemini {model} timed out. Triggering fallback.")
            raise RuntimeError("Gemini request timed out")
        except Exception as e:
            last_error = e
            logger.warning(f"[AI Engine] Gemini {model} error: {e}")
            break

    raise last_error or RuntimeError("Gemini failed to respond.")


def call_groq(prompt: str, api_key: str) -> dict:
    """Fast call to Groq Cloud (Free LPU inference)."""
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    last_error = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional Indian stock market analyst. Provide direct, objective technical & risk conclusions without boilerplate disclaimers.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 600,
        }

        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = (msg.get("content") or msg.get("reasoning") or "").strip()
                if content:
                    return {
                        "text": content,
                        "provider": "Groq (Free Fallback)",
                        "model": model,
                    }
            else:
                last_error = RuntimeError(f"Groq API {resp.status_code}: {resp.text[:150]}")
                logger.warning(f"[AI Engine] Groq {model} returned HTTP {resp.status_code}")
        except Exception as e:
            last_error = e
            logger.warning(f"[AI Engine] Groq {model} request failed: {e}")

    raise last_error or RuntimeError("Groq models failed to respond.")


def call_grok(prompt: str, api_key: str) -> dict:
    """Fast call to xAI Grok API."""
    if not api_key:
        raise ValueError("XAI_API_KEY is not configured.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    last_error = None
    for model in XAI_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional Indian stock market analyst. Provide direct, objective technical & risk conclusions without boilerplate disclaimers.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 400,
        }

        try:
            resp = requests.post(XAI_API_URL, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return {
                    "text": content,
                    "provider": "xAI Grok",
                    "model": model,
                }
            else:
                last_error = RuntimeError(f"xAI API {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            last_error = e
            logger.warning(f"[AI Engine] xAI {model} request failed: {e}")

    raise last_error or RuntimeError("xAI models failed to respond.")


def get_ai_conclusion(symbol: str, price_line: str, timeframe: str = "1D") -> dict:
    """
    Tier 1: Gemini
    Tier 2: Groq (Free fast inference)
    Tier 3: xAI Grok
    """
    gemini_key, groq_key, grok_key = get_keys()

    prompt = f"""You are a professional Indian stock market analyst.
Stock: {symbol} | Timeframe: {timeframe}
{price_line}

In exactly 4 sentences:
1. Current technical picture
2. Key support / resistance level to watch
3. Main risk right now
4. Final verdict — BUY, HOLD, WAIT, or SELL

Be direct. No disclaimers. End with the verdict word in capitals."""

    # 1. Try Primary: Gemini
    if gemini_key:
        try:
            res = call_gemini(prompt, gemini_key)
            return {
                "summary": res["text"],
                "provider": res["provider"],
                "model": res["model"],
                "fallback_triggered": False,
            }
        except Exception as e:
            logger.warning(f"[AI Engine] Primary Gemini failed ({e}). Switching to Groq fallback...")

    # 2. Try Fallback 1: Groq (Free & Fast)
    if groq_key:
        try:
            res = call_groq(prompt, groq_key)
            return {
                "summary": res["text"],
                "provider": res["provider"],
                "model": res["model"],
                "fallback_triggered": True,
            }
        except Exception as e:
            logger.warning(f"[AI Engine] Groq fallback failed: {e}")

    # 3. Try Fallback 2: xAI Grok (if key available)
    if grok_key and grok_key != groq_key:
        try:
            res = call_grok(prompt, grok_key)
            return {
                "summary": res["text"],
                "provider": res["provider"],
                "model": res["model"],
                "fallback_triggered": True,
            }
        except Exception as e:
            logger.warning(f"[AI Engine] xAI Grok fallback failed: {e}")

    # If neither key or fallback available
    if not groq_key:
        return {
            "summary": "Gemini is currently experiencing high demand (503). Add your free GROQ_API_KEY to .env to enable instant fallback.",
            "provider": "None",
            "model": "None",
            "fallback_triggered": False,
        }

    return {
        "summary": "AI services are currently busy. Please try again in a few moments.",
        "provider": "None",
        "model": "None",
        "fallback_triggered": True,
    }
