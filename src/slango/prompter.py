import json
import yaml
from pprint import pprint, pformat
from datetime import datetime

from sentence_transformers import SentenceTransformer


from .cases import fetch_and_summarize_case
from .laws import compress_law
from .llm import classify_question, get_relevant_paragraphs, run_final_prompt

from .database import get_database
from .queries import *


def get_detailed_instruct(task: str, query: str) -> str:
    return f'Instruct: {task}\nQuery: {query}'


def update_prompt_spr(prompt_id, spr):
    neodb = get_database("milz26")
    query = f"""
    MATCH (p:Prompt) WHERE elementId(p) = "{prompt_id}"
    SET p.spr = $spr
    """
    neodb.run_with_params(query, params={"spr": spr})


def get_prompt_spr(prompt_id):
    neodb = get_database("milz26")
    query = f"""
    MATCH (p:Prompt) WHERE elementId(p) = "{prompt_id}"
    RETURN p.spr as spr
    """
    df = neodb.run_query(query)
    return df.iloc[0]["spr"]


def update_prompt_embeddings(prompt_id, embeddings):
    neodb = get_database("milz26")
    query = f"""
    MATCH (p:Prompt) WHERE elementId(p) = "{prompt_id}"
    SET p.embeddings = $embeddings
    """
    neodb.run_with_params(query, params={"embeddings": embeddings})


def calculate_prompt_text_embeddings(prompt_text, model):
    # the model is trained to understand specific tasks in prompts
    # so we need to make sure that the prompt is in the correct format
    task = "Given a legal question, retrieve relevant passages that answer the question"
    full_prompt = get_detailed_instruct(task, prompt_text)
    embeddings = model.encode(
        [full_prompt], convert_to_tensor=False, normalize_embeddings=True
    )
    return embeddings[0]


def add_prompt(text):
    neodb = get_database("milz26")
    query = f"""
    MERGE (p:Prompt {{text: $text}})
    RETURN elementId(p) as prompt_id
    """
    df = neodb.run_with_params(query, params={"text": text})
    prompt_id = df.iloc[0]["prompt_id"]
    return prompt_id


def create_similarities(prompt_id, only_laws=False, only_cases=False):
    """create similarities between the prompt and the chunks, optionally only for specific labels"""
    neodb = get_database("milz26")
    # remove the old similarities
    q = f"""
    MATCH (p:Prompt)-[r:SimilarTo]->(:Chunk)
    WHERE elementId(p) = "{prompt_id}"
    DELETE r
    """
    neodb.run_query(q)
    print("Deleted old similarities")
    chunk_match_stmt = "MATCH (n:Chunk)-[:CHUNK_OF]->(cl)"
    if only_laws and only_cases:
        chunk_match_stmt += " WHERE 'Law' IN labels(cl) OR 'Case' IN labels(cl)"
    elif only_laws:
        chunk_match_stmt += " WHERE 'Law' IN labels(cl)"
    elif only_cases:
        chunk_match_stmt += " WHERE 'Case' IN labels(cl)"
    else:  # None
        chunk_match_stmt += " WHERE 1 = 1"
    chunk_match_stmt += " AND n.embeddings_e5 IS NOT NULL"
    q = f"""
    MATCH (p:Prompt)
    WHERE elementId(p) = "{prompt_id}"
    WITH p
    {chunk_match_stmt}
    WITH n, p, gds.similarity.cosine(n.embeddings_e5, p.embeddings_e5) as sim
    WHERE sim > 0.85
    MERGE (p)-[r:SimilarTo {{similarity_e5: sim}}]->(n)
    """
    print(q)
    neodb.run_query(q)


def get_laws_context_df(prompt_id, top_n=3):
    neodb = get_database("milz26")
    q = f"""
    MATCH (p:Prompt)-[r:SimilarTo]->(n:Chunk)-[:CHUNK_OF]->(cl:Law) WHERE elementId(p) = "{prompt_id}"
    RETURN elementId(n) as chunk_id, n.text as chunk_text, r.similarity_e5 as similarity, 
    elementId(cl) as law_id, 
    cl.code as law_code, cl.section as law_section, cl.content as law_content
    """
    print(q)
    df = neodb.run_with_params(q)

    # only top n similar laws
    df = (
        df.groupby([c for c in df.columns if c != "similarity"])
        .agg({"similarity": "mean"})
        .reset_index()
    )
    df = df.sort_values("similarity", ascending=False).head(top_n)
    return df


def get_cases_context_df(prompt_id, top_n=3):
    neodb = get_database("milz26")
    q = f"""
    MATCH (p:Prompt)-[r:SimilarTo]->(n:Chunk)-[:CHUNK_OF]->(cl:Case) WHERE elementId(p) = "{prompt_id}"
    RETURN elementId(n) as chunk_id, n.text as chunk_text, r.similarity_e5 as similarity, 
    elementId(cl) as case_id
    """
    print(q)
    df = neodb.run_with_params(q)

    # average the similarities for each case
    df = df.groupby("case_id").agg({"similarity": "mean"}).reset_index()
    df = df[["case_id", "similarity"]].drop_duplicates()
    df = df.sort_values("similarity", ascending=False).head(top_n)
    return df


def build_list_of_law_summaries(laws_df):
    # handle the laws
    list_of_laws = []
    for _ix, row in laws_df.iterrows():
        law_id = row["law_id"]
        spr = compress_law(law_id)
        law_dict = {
            "id": _ix,
            "Gesetzbuch": row["law_code"],
            "Paragraph": row["law_section"],
            "Zusammenfassung": spr,
        }
        list_of_laws.append(law_dict)
    return list_of_laws


def build_list_of_case_summaries(cases_df):
    list_of_cases = []
    for _ix, row in cases_df.iterrows():
        case_id = row["case_id"]
        summary, case_type, case_date, case_file_number = fetch_and_summarize_case(
            case_id
        )
        case_dict = {
            "id": _ix,
            "Fallnummer": case_file_number,
            "Datum": case_date.strftime("%Y-%m-%d"),
            "Falltyp": case_type,
            "Zusammenfassung": summary,
        }
        list_of_cases.append(case_dict)
    return list_of_cases


def full_workflow():
    print("Loading embeddings model...")
    model = SentenceTransformer(
        'intfloat/multilingual-e5-large-instruct', device="cuda"
    )
    # prompt_text = "Die Bäume meines Nachbarn ragen in mein Grundstück. Auf einigen der Bäume wachsen Äpfel. Darf ich die Äpfel pflücken, die an den Ästen wachen, die in mein Grundstück ragen?"
    # prompt_text = "Mein Vermiter möchte meine Wohnung anschauen, aber ich habe keine Lust auf Besuch. Muss ich ihn reinlassen? "
    # prompt_text = "Muss ich die Reparaturkosten für meine Mietwohnung übernehmen, wenn ich den Schaden nicht verursacht habe und der Vermieter die Wohnung nicht ordnungsgemäß instand gehalten hat?"
    # prompt_text = "Mein Nachbar spielt jede Nacht laut Musik und stört meine Ruhe. Kann ich ihn wegen Lärmbelästigung verklagen?"
    # prompt_text = "Ich war in einen Autounfall verwickelt und die Versicherung des anderen Beteiligten bietet mir eine Entschädigung an. Muss ich ihr Angebot annehmen oder kann ich um ein höheres Entgelt verhandeln?"
    # prompt_text = "Ich bin Freiberufler und mein Kunde weigert sich, mich für die geleistete Arbeit zu bezahlen. Kann ich ihn vor Gericht bringen, um mein Geld zu bekommen?"
    # prompt_text = "Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?"
    # prompt_text = "Darf ich ein Gespräch mit meinem Chef heimlich aufzeichnen, wenn ich mich belästigt fühle?"
    # prompt_text = "Ich habe ein Produkt online gekauft, das sich als defekt herausgestellt hat. Kann ich es zurückgeben und eine volle Rückerstattung erhalten?"
    # prompt_text = "Ich bin Ausländer und wurde abgeschoben. Kann ich gegen die Abschiebung klagen?"
    # prompt_text = "أنا أجنبي وأريد العمل في ألمانيا. ما نوع التأشيرة التي أحتاجها؟"
    # prompt_text = QUERY1
    # prompt_text = QUERY2
    # prompt_text = QUERY3
    prompt_text = QUERY4
    # prompt_text = QUERY5

    prompt_id = add_prompt(prompt_text)
    print(prompt_id)
    prompt_class = classify_question(
        prompt_text,
        categories={
            1: "The question can be answered based on law texts without considering court rulings",
            2: "The question can be answered based on court rulings without considering law texts",
            3: "The question requires knowledge of both law texts and court rulings in order to be answered",
        },
    )
    print(prompt_class)
    # remove the ``` from the begiing and end of the string
    prompt_class = prompt_class.replace("```", "")
    prompt_class = json.loads(prompt_class)
    prompt_cat = prompt_class["category_id"]
    if prompt_cat == "1":
        laws = 15
        cases = 0
    elif prompt_cat == "2":
        laws = 0
        cases = 4
    else:
        laws = 10
        cases = 2
    print("Calculating similarities...")
    create_similarities(prompt_id, only_laws=(laws > 0), only_cases=(cases > 0))
    print("Done calculating similarities...")

    cases_df = get_cases_context_df(prompt_id, top_n=cases)
    laws_df = get_laws_context_df(prompt_id, top_n=laws)
    law_summaries = build_list_of_law_summaries(laws_df)
    case_summaries = build_list_of_case_summaries(cases_df)
    law_parlist = [
        {
            "paragraph_id": laws_df.iloc[i]['law_id'],
            "paragraph_summary": f"{law['Gesetzbuch']} {law['Paragraph']}: {law['Zusammenfassung']}",
        }
        for i, law in enumerate(law_summaries)
    ]
    case_parlist = [
        {
            "paragraph_id": cases_df.iloc[i]['case_id'],
            "paragraph_summary": f"{case['Fallnummer']} ({case['Datum']}): {case['Zusammenfassung']}",
        }
        for i, case in enumerate(case_summaries)
    ]
    full_parlist = law_parlist + case_parlist
    full_dict = {"input_text": prompt_text, "paragraphs": full_parlist}
    content = yaml.dump(full_dict, allow_unicode=True, width=150)
    relpars = get_relevant_paragraphs(prompt_text, full_parlist, n=7)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"full_prompt_{timestamp}.md", "w") as f:
        f.write("\n## Relevance choice prompt\n")
        f.write("\n### prompt\n")
        f.write(content)
        f.write("\n### response\n")
        f.write(relpars)
    # are the relpars positions in the list?
    positional_relpars = False
    try:
        relpars = json.loads(relpars.replace("`", ""))
        relpars = [int(rp) for rp in relpars]
        positional_relpars = True
    except (json.JSONDecodeError, ValueError):
        pass

    # expand the relevant ones, keep the rest
    print("Expanding the relevant paragraphs...")
    relevant_laws = []
    for i, _id in enumerate(laws_df["law_id"].tolist()):
        if _id in relpars or (positional_relpars and i in relpars):
            relevant_laws.append(_id)
    relevant_laws_df = laws_df[laws_df["law_id"].isin(relevant_laws)]
    relevant_law_contents = [
        {f"{row['law_code']} {row['law_section']}: {row['law_content']}"}
        for name, row in relevant_laws_df.iterrows()
    ]
    full_context = relevant_law_contents + [
        ls["paragraph_summary"]
        for ls in law_parlist
        if ls["paragraph_id"] not in relevant_laws
    ]
    full_context += case_summaries

    full_dict = {"User question": prompt_text, "context": full_context}
    full_prompt = yaml.dump(full_dict, allow_unicode=True, width=150)
    # save the prompt to a file with timestamp
    with open(f"full_prompt_{timestamp}.md", "a") as f:
        f.write("\n## Final prompt\n")
        f.write("\n### prompt\n")
        f.write(full_prompt)

    # run the final prompt
    final_response = run_final_prompt(full_prompt)
    with open(f"full_prompt_{timestamp}.md", "a") as f:
        f.write("\n### response\n")
        f.write(final_response)


if __name__ == "__main__":
    full_workflow()
