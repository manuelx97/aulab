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
    def create_prompt(context, question):
        return f"""
            Dato il seguente contesto:
            [[[
            {context}
            ]]].
            Rispondi alla domanda dell'utente: [[[ {question} ]]].
            Spiega che nel file individuato c'e' il profilo piu' adatto.
            Argomenta la scelta utilizzando il contenuto del testo individuato nel contesto.
            Se non trovi corrispondenza in nessun cv non inventare.
            Alla fine crea una sezione per i contatti del candidato indicando il nome,
            la sua email e il numero di telefono, se presenti nel contesto.
            Dopo la sezione dei contatti indica il nome del file del cv.
        """
