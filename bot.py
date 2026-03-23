import time
import requests
import os
from bs4 import BeautifulSoup

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("Erro: TOKEN ou CHAT_ID não definidos")
    exit()

# ===== TELEGRAM =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    print(response.text)

# ===== CONFIG BUSCA =====
BASE_URL = "https://www.linkedin.com/jobs/search/?keywords=ux%20designer&location=Brazil"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

seen_jobs = set()

# ===== FILTROS =====
GOOD_KEYWORDS = ["ux", "ui", "product designer"]

GOOD_LEVELS = ["junior", "jr", "intern", "estagio", "trainee", "entry"]

BAD_TERMS = [
    "senior", "pleno", "lead", "manager", "coordinator",
    "pcd", "pessoa com deficiência", "afirmativa", "affirmative"
]

NO_EXPERIENCE_TERMS = [
    "no experience", "sem experiência", "entry level",
    "junior sem experiencia", "não requer experiência"
]

FAKE_TERMS = [
    "ganhos ilimitados", "trabalhe de casa fácil",
    "sem experiência necessária com altos ganhos",
    "renda extra imediata", "início imediato"
]

LOCATION_TERMS = [
    "remote", "remoto", "anywhere", "brazil", "brasil",
    "curitiba", "paraná", "cwb",
    "hybrid", "híbrido"
]

GOOD_COMPANIES = [
    "nubank", "ifood", "ebanx", "xp",
    "mercado livre", "stone", "loft"
]

# ===== IA DE AVALIAÇÃO =====
def evaluate_job(description):
    score = 0
    reasons = []

    d = description.lower()

    if "junior" in d or "entry" in d:
        score += 2
        reasons.append("nível adequado")

    if "estágio" in d or "intern" in d:
        score += 3
        reasons.append("estágio")

    if any(term in d for term in ["sem experiência", "no experience"]):
        score += 4
        reasons.append("não exige experiência")

    if any(tool in d for tool in ["figma", "ux research", "wireframe", "prototype"]):
        score += 1
        reasons.append("stack relevante")

    if "2 anos" in d or "3 anos" in d or "+2" in d:
        score -= 3
        reasons.append("pede experiência")

    if any(term in d for term in ["senior", "lead", "pleno"]):
        score -= 5
        reasons.append("nível acima")

    if any(term in d for term in ["alta pressão", "multitarefa extrema", "ganhos ilimitados"]):
        score -= 2
        reasons.append("red flag")

    if score >= 4:
        decision = "✅ VALE APLICAR"
    elif score >= 1:
        decision = "🤔 TALVEZ"
    else:
        decision = "❌ NÃO VALE"

    return decision, score, reasons

# ===== FILTRO TÍTULO =====
def is_good_title(title):
    t = title.lower()

    if not any(k in t for k in GOOD_KEYWORDS):
        return False

    if not any(l in t for l in GOOD_LEVELS):
        return False

    if any(b in t for b in BAD_TERMS):
        return False

    return True

# ===== FILTRO TEMPO (NOVO 🔥) =====
def is_recent(job_element):
    try:
        time_element = job_element.find("time")
        if not time_element:
            return True

        text = time_element.text.lower()

        # ignora vagas antigas
        if "day" in text and not "1 day" in text:
            return False
        if "week" in text:
            return False
        if "month" in text:
            return False

        return True
    except:
        return True

# ===== ANALISAR VAGA =====
def analyze_job_page(link):
    try:
        response = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        description = soup.get_text(" ").lower()

        if not any(loc in description for loc in LOCATION_TERMS):
            return False, None, None, None

        if any(f in description for f in FAKE_TERMS):
            return False, None, None, None

        decision, score, reasons = evaluate_job(description)

        no_exp = any(term in description for term in NO_EXPERIENCE_TERMS)

        return True, no_exp, decision, (score, reasons)

    except:
        return False, None, None, None

# ===== BUSCAR VAGAS =====
def check_jobs():
    response = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = soup.find_all("li")

    for job in jobs:
        link_tag = job.find("a", class_="base-card__full-link")
        if not link_tag:
            continue

        title = link_tag.text.strip()
        link = link_tag["href"]

        # 🔥 NOVO FILTRO DE TEMPO
        if not is_recent(job):
            continue

        if link in seen_jobs:
            continue

        if not is_good_title(title):
            continue

        seen_jobs.add(link)

        valid, no_exp, decision, extra = analyze_job_page(link)

        if not valid:
            continue

        score, reasons = extra

        badge_exp = "🟢 SEM EXPERIÊNCIA\n" if no_exp else ""

        badge_company = ""
        if any(c in title.lower() for c in GOOD_COMPANIES):
            badge_company = "🏆 EMPRESA TOP\n"

        reasons_text = ", ".join(reasons[:3])

        message = f"""{badge_company}{badge_exp}🔥 Nova vaga UX/UI

📌 {title}

{decision} (score: {score})

🧠 Motivos: {reasons_text}

🌎 Remoto BR / Curitiba / Híbrido
🎯 Junior / Estágio

🔗 {link}
"""

        print(message)
        send_telegram(message)

# ===== LOOP =====
while True:
    print("🔄 Buscando vagas...")
    check_jobs()
    time.sleep(180)
