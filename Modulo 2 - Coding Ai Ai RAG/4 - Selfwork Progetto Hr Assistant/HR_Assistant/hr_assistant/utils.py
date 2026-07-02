import ollama

from hr_assistant.config import Config


class LLMHelper:
    @staticmethod
    def chat(messages):
        return ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=messages,
            stream=True,
        )

    @staticmethod
    def get_candidate_name(context):
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Dato il seguente contesto individua il nome e cognome "
                        "del candidato e ritorna solo il nome e cognome del candidato. "
                        f"Il contesto e' l'inizio del curriculum vitae: {context}"
                    ),
                }
            ],
        )

        return response["message"]["content"]

    @staticmethod
    def get_db_stats(context):
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Descrivi in modo sintetico e chiaro le statistiche "
                        "del database dei frammenti indicizzati da questo sistema. "
                        f"Ecco le informazioni disponibili: {context}"
                    ),
                }
            ],
        )

        return response["message"]["content"]

    @staticmethod
    def classify_intent(user_question):
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Classifica la richiesta dell'utente in una sola categoria. "
                        "Rispondi esclusivamente con search_cv se l'utente sta cercando "
                        "un candidato con determinate competenze. Rispondi esclusivamente "
                        "con info_cv se l'utente sta chiedendo informazioni su un candidato "
                        "o curriculum gia' individuato nella conversazione. "
                        f"Richiesta: {user_question}"
                    ),
                }
            ],
        )
        intent = response["message"]["content"].strip().lower()

        if "info_cv" in intent:
            return "info_cv"

        return "search_cv"

    @staticmethod
    def create_prompt(context, question, candidate_info=None, intent="search_cv"):
        return f"""
            Sei un assistente esperto nella selezione del personale.

            Contesto disponibile:
            [[[
            {context}
            ]]].

            Informazioni iniziali del CV:
            [[[
            {candidate_info or "Non disponibili"}
            ]]]

            Domanda dell'utente:
            [[[ {question} ]]]

            Intento classificato: {intent}

            Se l'intento e' search_cv:
            - spiega che nel file individuato c'e' il profilo piu' adatto;
            - argomenta la scelta usando competenze ed esperienze rilevanti;
            - alla fine crea una sezione per i contatti del candidato;
            - dopo i contatti indica il nome del file del cv.

            Se l'intento e' info_cv:
            - rispondi solo alla domanda specifica sul CV gia' individuato;
            - evita dettagli non richiesti;
            - se l'informazione non e' nel contesto, dichiaralo chiaramente.

            Scrivi in italiano corretto e non inventare informazioni.
        """
