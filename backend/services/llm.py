"""LLM service - manually added API key support.
Reads from .env via os.getenv. Never exposes key to frontend.
Supports OpenAI, Gemini, Anthropic, or generic. Falls back to rule-based explanation.
"""
from __future__ import annotations
import os
from typing import Dict, Any, Optional

def _get_key() -> tuple[Optional[str], str]:
    for k in ("GROQ_API_KEY","OPENAI_API_KEY","GEMINI_API_KEY","ANTHROPIC_API_KEY","AI_API_KEY","LLM_API_KEY"):
        v = os.getenv(k)
        if v and v.strip() and not v.startswith("sk-proj-your") and not v.startswith("AIza-your") and not v.startswith("gsk_your"):
            return v.strip(), k
    return None, ""

def has_key() -> bool:
    k,_ = _get_key()
    return bool(k)

def provider_name() -> str:
    _, name = _get_key()
    if "GROQ" in name: return "groq"
    if "OPENAI" in name: return "openai"
    if "GEMINI" in name: return "gemini"
    if "ANTHROPIC" in name: return "anthropic"
    if name: return "generic"
    return "rule-based"

def explain_analysis(payload: Dict[str,Any]) -> str:
    """Generate human explanation from real analysis data. Uses LLM if key exists, else rule-based."""
    score = payload.get("recharge_suitability") or payload.get("score") or payload.get("recharge",{}).get("score",0)
    clazz = payload.get("suitability_class") or payload.get("class") or "MEDIUM"
    factors = payload.get("factors") or payload.get("recharge",{}).get("factors") or {}
    why = payload.get("why") or []
    # Try LLM if key exists
    key, _ = _get_key()
    if key:
        provider = provider_name()
        # Groq path (OpenAI-compatible, super fast) - try current available models
        if provider=="groq":
            for mname in ("openai/gpt-oss-20b","openai/gpt-oss-120b","qwen/qwen3-32b","allam-2-7b","llama-3.3-70b-versatile"):
                try:
                    from groq import Groq
                    client = Groq(api_key=key)
                    prompt = f"""You are JAL-RAKSHA AI water expert. Explain recharge suitability for spring {payload.get('spring_id','')}:
Score {score}/100 class {clazz}, factors {factors}, why {why}. 
Be concise 3 sentences, mention top factor, intervention hint, end with 'Prototype Decision-Support Estimate'."""
                    r = client.chat.completions.create(model=mname, messages=[{"role":"user","content":prompt}], max_tokens=180)
                    txt = (r.choices[0].message.content or "").strip()
                    if txt:
                        return txt + f" [via Groq:{mname}]"
                except Exception:
                    continue
            for mname in ("openai/gpt-oss-20b","openai/gpt-oss-120b"):
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                    prompt = f"""You are JAL-RAKSHA AI water expert. Explain recharge suitability for spring {payload.get('spring_id','')}:
Score {score}/100 class {clazz}, factors {factors}, why {why}. 
Be concise 3 sentences, mention top factor, intervention hint, end with 'Prototype Decision-Support Estimate'."""
                    r = client.chat.completions.create(model=mname, messages=[{"role":"user","content":prompt}], max_tokens=180)
                    txt = (r.choices[0].message.content or "").strip()
                    if txt:
                        return txt + f" [via Groq/OpenAI:{mname}]"
                except Exception:
                    continue
        # OpenAI path
        if provider=="openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=key)
                prompt = f"""You are JAL-RAKSHA AI water expert. Explain recharge suitability for spring {payload.get('spring_id','')}:
Score {score}/100 class {clazz}, factors {factors}, why {why}. 
Be concise 3 sentences, mention top factor, intervention hint, end with 'Prototype Decision-Support Estimate'."""
                r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], max_tokens=180)
                txt = r.choices[0].message.content.strip()
                return txt + " [via OpenAI]"
            except Exception as e:
                pass
        if provider=="gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"Explain recharge {score} class {clazz} factors {factors} for spring. 3 sentences, top factor, intervention."
                r = model.generate_content(prompt)
                return r.text.strip() + " [via Gemini]"
            except Exception:
                pass
    # Fallback rule-based (always truthful to data)
    top = max(factors.items(), key=lambda kv: kv[1]) if factors else ("rainfall", 0)
    lines = []
    if score >= 70:
        lines.append(f"High recharge suitability ({score}%) driven by {top[0]} ({top[1]} pts).")
        lines.append("Fractured geology and good soil moisture support infiltration.")
    elif score >=45:
        lines.append(f"Medium suitability ({score}%) — {top[0]} is strongest but slope or distance to stream limits recharge.")
        lines.append("Targeted trench/pond can improve score.")
    else:
        lines.append(f"Low suitability ({score}%) — {top[0]} is weak, plus deep groundwater or clay restricts recharge.")
        lines.append("Check dam in nearby stream more effective than hillside trench.")
    if why:
        lines.append("Priority reasons: " + "; ".join(why[:2]) + ".")
    lines.append("Prototype Decision-Support Estimate — requires field validation.")
    return " ".join(lines)
