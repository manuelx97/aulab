from openai import OpenAI
from pydantic import BaseModel
from enum import Enum
from dotenv import load_dotenv

load_dotenv('.env')

MODEL = "gpt-4o"
client = OpenAI()


# ─────────────────────────────────────────────
# 1. SCHEMA PYDANTIC  (con Enum come nella lezione)
# ─────────────────────────────────────────────

class Priorita(str, Enum):
    bassa   = "bassa"
    media   = "media"
    alta    = "alta"
    critica = "critica"

class Categoria(str, Enum):
    fatturazione = "fatturazione"
    tecnico      = "tecnico"
    account      = "account"
    spedizione   = "spedizione"
    altro        = "altro"

class Ticket(BaseModel):
    categoria: Categoria
    priorita: Priorita
    problema_breve: str            
    azione_suggerita: str          
    dati_da_richiedere: list[str]  
    sentiment: str                

    def stampa(self):
        emoji_priorita = {"bassa": "🟢", "media": "🟡", "alta": "🟠", "critica": "🔴"}
        print(f"\n{'─'*55}")
        print(f"  {emoji_priorita[self.priorita.value]} Priorità: {self.priorita.value.upper()}"
              f"  |  Categoria: {self.categoria.value}")
        print(f"{'─'*55}")
        print(f"  Problema:  {self.problema_breve}")
        print(f"  Sentiment: {self.sentiment}")
        print(f"\n   Azione suggerita:")
        print(f"     {self.azione_suggerita}")
        if self.dati_da_richiedere:
            print(f"\n   Dati da richiedere al cliente:")
            for d in self.dati_da_richiedere:
                print(f"     - {d}")
        print()


# ─────────────────────────────────────────────
# 2. TICKET DI ESEMPIO
# ─────────────────────────────────────────────

tickets = [
    {
        "id": "TK-001",
        "testo": """
        Buongiorno, ho effettuato un ordine la settimana scorsa ma non ho ancora
        ricevuto nulla. Sul sito risulta 'spedito' ma il codice tracking non funziona.
        Ho bisogno del pacco entro venerdì per un regalo di compleanno urgente!
        """
    },
    {
        "id": "TK-002",
        "testo": """
        Non riesco ad accedere al mio account. Ho provato a reimpostare la password
        tre volte ma non ricevo l'email di reset. Ho un abbonamento attivo che sto
        pagando e non riesco ad usare il servizio. Questo è inaccettabile!!
        """
    },
    {
        "id": "TK-003",
        "testo": """
        Salve, vorrei sapere se è possibile cambiare il piano di abbonamento
        dal mensile all'annuale. Grazie mille per l'aiuto.
        """
    },
]


# ─────────────────────────────────────────────
# 3. 
# ─────────────────────────────────────────────

system_prompt = """
Sei un sistema di triage per l'assistenza clienti.
Analizza il messaggio del cliente e classifica il ticket seguendo lo schema.
"""

def classifica_ticket(testo: str) -> Ticket:
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": testo}
        ],
        response_format=Ticket,
    )

    msg = completion.choices[0].message

    # Gestione refusal 
    if msg.refusal:
        print(f"  Refusal: {msg.refusal}")
        return None

    return msg.parsed


# ─────────────────────────────────────────────
# 4. ELABORAZIONE STAMPA
# ─────────────────────────────────────────────

print("\\ SISTEMA DI TRIAGE TICKET")

risultati = []
for t in tickets:
    print(f"\nAnalisi ticket {t['id']}...")
    ticket = classifica_ticket(t["testo"])
    risultati.append({"id": t["id"], "ticket": ticket})
    ticket.stampa()

# Riepilogo ordinato per priorità
ORDINE = ["critica", "alta", "media", "bassa"]
print("\n" + "="*55)
print("  RIEPILOGO ORDINATO PER PRIORITÀ")
print("="*55)
for priorita in ORDINE:
    gruppo = [r for r in risultati if r["ticket"] and r["ticket"].priorita.value == priorita]
    if gruppo:
        for r in gruppo:
            print(f"  [{r['id']}] {priorita.upper():8s} – {r['ticket'].problema_breve}")
print()
