from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv('.env')

MODEL = "gpt-4o"
client = OpenAI()


# ─────────────────────────────────────────────
# 1. SCHEMA PYDANTIC
# ─────────────────────────────────────────────

class Esperienza(BaseModel):
    azienda: str
    ruolo: str
    anni: int              
    competenze: list[str]  

class CV(BaseModel):
    nome: str
    anni_esperienza_totale: int
    livello_seniority: str         
    linguaggi_programmazione: list[str]
    esperienze: list[Esperienza]
    punti_di_forza: list[str]      

    def stampa(self):
        print(f"\n{'='*50}")
        print(f"  {self.nome}  —  {self.livello_seniority}")
        print(f"{'='*50}")
        print(f"Esperienza totale: {self.anni_esperienza_totale} anni")
        print(f"Linguaggi:         {', '.join(self.linguaggi_programmazione)}")
        print(f"\nPunti di forza:")
        for p in self.punti_di_forza:
            print(f"  ✓ {p}")
        print(f"\nEsperienze lavorative:")
        for e in self.esperienze:
            print(f"  [{e.anni}a] {e.ruolo} @ {e.azienda}")
            print(f"        Skills: {', '.join(e.competenze)}")
        print()


# ─────────────────────────────────────────────
# 2. CURRICULUM DI ESEMPIO (testo libero)
# ─────────────────────────────────────────────

cv_testo = """
Mi chiamo Marco Ferretti. Ho iniziato la mia carriera come sviluppatore junior
nel 2015 in una startup di e-commerce a Milano, dove ho lavorato per 2 anni
con Python e Django per il backend.

Successivamente sono passato a TechCorp (2017-2020), una software house
dove ho ricoperto il ruolo di Software Engineer. Lì ho approfondito
FastAPI, PostgreSQL e Docker, partecipando a progetti per clienti bancari.

Dal 2020 lavoro come Senior Backend Engineer in CloudSoft, dove coordino
un team di 3 sviluppatori junior. Utilizzo principalmente Python, Kubernetes
e AWS. Ho introdotto pratiche di CI/CD e code review sistematiche.

Sono appassionato di architetture a microservizi e amo mentorare i colleghi.
Parlo italiano e inglese fluentemente.
"""

# ─────────────────────────────────────────────
# 3. 
# ─────────────────────────────────────────────

system_prompt = """
Sei un esperto di recruiting tecnico.
Analizza il CV fornito ed estrai le informazioni seguendo lo schema.
"""

def analizza_cv(testo: str) -> CV:
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": testo}
        ],
        response_format=CV,
    )
    return completion.choices[0].message.parsed


# ─────────────────────────────────────────────
# 4. PARSING E VISUALIZZAZIONE
# ─────────────────────────────────────────────

result = analizza_cv(cv_testo)

# Gestione refusal 
if result is None:
    print("Il modello ha rifiutato di elaborare il CV.")
else:
    result.stampa()

