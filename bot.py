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

send_telegram("🚀 TESTE: bot funcionando")

BASE_URL = "https://www.linkedin.com/jobs/search/?keywords=ux%20designer&location=Brazil"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

seen_jobs = set()

# ===== FILTROS =====
GOOD_KEYWORDS = ["ux", "ui", "product designer"]

GOOD_LEVELS = ["junior", "jr", "intern", "estagio", "trainee", "entry"]

BAD_WORDS = ["senior", "pleno", "lead", "manager", "coordinator"]

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
    "remote", "remoto", "curitiba"
]

# ===== TELEGRAM =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ===== FILTRO TÍTULO =====
def is_good_title(title):
    t = title.lower()

    if not any(k in t for k in GOOD_KEYWORDS):
        return False

    if not any(l in t for l in GOOD_LEVELS):
        return False

    if any(b in t for b in BAD_WORDS):
        return False

    return True

# ===== ANALISAR DESCRIÇÃO =====
def analyze_job_page(link):
    try:
        response = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        description = soup.get_text(" ").lower()

        # localização
        if not any(loc in description for loc in LOCATION_TERMS):
            return False, "📍 Fora do filtro (não é remoto/Curitiba)"

        # fake
        if any(f in description for f in FAKE_TERMS):
            return False, "🚫 Possível vaga fake"

        # experiência
        no_exp = any(term in description for term in NO_EXPERIENCE_TERMS)

        return True, no_exp

    except:
        return False, "Erro ao analisar"

# ===== BUSCAR VAGAS =====
def check_jobs():
    response = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = soup.find_all("a", class_="base-card__full-link")

    for job in jobs:
        title = job.text.strip()
        link = job["href"]

        if link in seen_jobs:
            continue

        if not is_good_title(title):
            continue

        seen_jobs.add(link)

        valid, info = analyze_job_page(link)

        if not valid:
            continue

        badge = "🟢 SEM EXPERIÊNCIA\n" if info else ""

        message = f"""{badge}🔥 Nova vaga UX/UI:
{title}
{link}
"""

        print(message)
        send_telegram(message)

# ===== LOOP =====
while True:
    check_jobs()
    time.sleep(180)
