import json
import chainlit as cl
from datetime import date
from openai import OpenAI
from config import Config
from prompts import query_writer_instruction,summerize_instruction,reflection_instructions
from tavily import TavilyClient

client = OpenAI(base_url=Config.AI_API_URL, api_key=Config.AI_API_KEY)



def llm(developer_promt, user_prompt, temperature=0, response_format={"type": "json_object"}):
    response = client.chat.completions.create(
        model=Config.LLM_MODEL_LOW,
        messages=[
            {"role": "developer", "content": developer_promt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format=response_format
    )
    return response.choices[0].message.content


def optimize_search_query(research_topic):
    current_date = date.today().strftime("%Y-%m-%d")
    formatted_instruction = query_writer_instruction.format(
        research_topic=research_topic,
        current_date=current_date,
    )
    result = llm(formatted_instruction, "Genera una query per la ricerca web:")
    obj = json.loads(result)
    return obj

def _format_content(result):
    return f"""
    Fonte: {result['title']}:\n===\n
    Url: {result['url']}\n===\n
    Contenuto più rilevante: {result['content']}\n===\n
    """
    

def web_research(query):
    tavily_client = TavilyClient(api_key=Config.TAVILY_KEY)
    max_results = 3
    include_raw_ = True
    current_date = date.today().strftime("%Y-%m-%d")
    query_with_date = f"{query} aggiornato al {current_date}"
    response = tavily_client.search(query=query_with_date, max_results=max_results, include_raw_content=include_raw_)
    results = response.get("results", [])
    titles = [result.get("title", "No title") for result in results]
    contents = [_format_content(result) for result in results]
    return {
        "sources_gathered": titles,
        "web_search_results": contents
    }

def summarize_sources(web_research_results, research_topic, running_summary=None):
    #ultimo risultato
    current_results = "\n".join(web_research_results)

    if running_summary:
        message = (f"Estendi questo riassunto: {running_summary}\n\n"
                   f"con questi nuovi risultati: {current_results}\n\n"
                   f"sul tema di ricerca: {research_topic}")
    else:
        message = (f"Genera un riassunto di questi risultati: {current_results}\n\n"
                   f"sul tema di ricerca: {research_topic}")
        
        
    output_formatter = None
    return llm(summerize_instruction,message, 0, output_formatter)

def reflect_on_summary(research_topic, running_summary):
    formatted_instruction = reflection_instructions.format(research_topic=research_topic)
    result = llm(formatted_instruction, f"identifica una lacuna e genera una domanda per la prossima ricerca basandosi su: {running_summary}")
    return json.loads(result) 

@cl.on_message
async def main(message: cl.Message):
    user_message = message.content
    
    try:
        osq = optimize_search_query(user_message)
        query, aspect, reason = osq["query"], osq["aspect"], osq["reason"]
        await cl.Message(
            author="system_assistant",
            content=f"Query ottimizzata:\n {query}\nAspetto: {aspect}\nMotivo: {reason}",
        ).send()

        running_summary = None
        max_cicles = 2

        while True:
            results = web_research(query)
            titles = "\n".join(results['sources_gathered'])
            await cl.Message(author="system_assistant", content=f"Fonti trovate:\n {titles}").send()

            summary = summarize_sources(results['web_search_results'], query, running_summary)
            running_summary = summary
            await cl.Message(author="system_assistant", content=f"Riassunto:\n {summary}").send()

            max_cicles -= 1
            if max_cicles <= 0:
                # ✅ Messaggio finale PRIMA del break, quando summary è certamente disponibile
                await cl.Message(
                    author="segugio_assistant",
                    content=f"Risposta alla tua domanda:\n\n{user_message}\n\nRisposta finale:\n{summary}",
                ).send()
                break

            ros = reflect_on_summary(query, summary)
            query = ros.get('domanda_approfondimento', f'dimmi di più su {query}')
            lacuna = ros.get('lacuna_conoscenza', '')
            await cl.Message(
                author="system_assistant",
                content=f"Prossima ricerca:\n {query}\nPerché:\n {lacuna}",
            ).send()

    except Exception as e:
        await cl.Message(
            author="system_assistant",
            content=f"❌ Errore durante la ricerca: {str(e)}",
        ).send()
    user_message = message.content
    osq = optimize_search_query(user_message)
    query, aspect, reason = osq["query"], osq["aspect"], osq["reason"]
    # Send a response back to the user
    await cl.Message(author="system_assistant",
        content=f"Query di ricerca ottimizata:\n {query}\nMi sono soffermato su questo aspetto specifico: {aspect}\nPer questo motivo: {reason}",
    ).send()

    running_summary = None
    max_cicles = 2

    while True:

        results = web_research(query)
        titles = "\n".join(results['sources_gathered'])
        await cl.Message(author="system_assistant",
                        content=f"Fonti trovate:\n {titles}",
                    ).send()                     

        summary = summarize_sources(results['web_search_results'], query, running_summary)
        running_summary = summary

        await cl.Message(author="system_assistant",
                        content=f"Riassunto:\n {summary}"
                    ).send()    
        
        max_cicles -= 1
        if max_cicles <= 0:
            break
        
        ros = reflect_on_summary(query, summary)
        query = ros.get('domanda_approfondimento', f'dimmi di più su {query}')
        lacuna_conoscenza = ros.get('lacuna_conoscenza', '')

        await cl.Message(author="system_assistant",
                            content=f"Prossima ricerca:\n {query}\nMi sono soffermato su questo perchè:\n {lacuna_conoscenza}",
                        ).send()        
                    
    await cl.Message(author="segugio_assistant",
                        content=f"Risposta alla tua domanda:\n\n{message.content}\n\nRisposta finale: {summary}",
                    ).send()        
