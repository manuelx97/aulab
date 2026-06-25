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
    def create_prompt(context, question, candidate_name):
        return f"""
            Dato il seguente contesto:
            [[[
            {context}
            ]]].
            Rispondi alla domanda dell'utente: [[[ {question} ]]].
            Spiega che nel file individuato c'e' il profilo piu' adatto.
            Assicurati di nominare il nome del file.
            Assicurati di indicare il nome del candidato: [[[ {candidate_name} ]]].
            Argomenta la scelta utilizzando il contenuto del testo individuato nel contesto.
            Se non trovi corrispondenza in nessun cv non inventare.
        """
