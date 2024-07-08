import json
from openai import OpenAI

from .queries import QUERY5


def classify_question(question_text, categories):
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    full_dict = {
        "input_text": [question_text],
        "categories": categories,
        "classification_instructions": [],
    }
    completion = client.chat.completions.create(
        model="MaziyarPanahi/Llama-3-8B-Instruct-64k-GGUF",
        # model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        messages=[
            {
                "role": "system",
                "content": "\n    ### Job Description',\n    You are a text classification engine that analyzes text data and assigns categories based on user input or automatically determined categories.\n    ### Task\n    Your task is to assign one categories ONLY to the input text and only one category may be assigned returned in the output.Additionally, you need to extract the key words from the text that are related to the classification.\n    ### Format\n    The input text is in the variable input_text.Categories are specified as a category list with two filed category_id and category_name in the variable categories .Classification instructions may be included to improve the classification accuracy.\n    ### Constraint\n    DO NOT include anything other than the JSON array in your response.\n    ### Memory\n    Here is the chat histories between human and assistant, inside <histories></histories> XML tags.\n    <histories>\n    \n    </histories>\n",
            },
            {
                "role": "user",
                "content": '\n    { "input_text": ["I recently had a great experience with your company. The service was prompt and the staff was very friendly."],\n    "categories": [{"category_id":"f5660049-284f-41a7-b301-fd24176a711c","category_name":"Customer Service"},{"category_id":"8d007d06-f2c9-4be5-8ff6-cd4381c13c60","category_name":"Satisfaction"},{"category_id":"5fbbbb18-9843-466d-9b8e-b9bfbb9482c8","category_name":"Sales"},{"category_id":"23623c75-7184-4a2e-8226-466c2e4631e4","category_name":"Product"}],\n    "classification_instructions": ["classify the text based on the feedback provided by customer"]}\n',
            },
            {
                "role": "assistant",
                "content": '\n```json\n    {"keywords": ["recently", "great experience", "company", "service", "prompt", "staff", "friendly"],\n    "category_id": "f5660049-284f-41a7-b301-fd24176a711c",\n    "category_name": "Customer Service"}\n```\n',
            },
            {
                "role": "user",
                "content": '\n    {"input_text": ["bad service, slow to bring the food"],\n    "categories": [{"category_id":"80fb86a0-4454-4bf5-924c-f253fdd83c02","category_name":"Food Quality"},{"category_id":"f6ff5bc3-aca0-4e4a-8627-e760d0aca78f","category_name":"Experience"},{"category_id":"cc771f63-74e7-4c61-882e-3eda9d8ba5d7","category_name":"Price"}],\n    "classification_instructions": []}\n',
            },
            {
                "role": "assistant",
                "content": '\n```json\n    {"keywords": ["bad service", "slow", "food", "tip", "terrible", "waitresses"],\n    "category_id": "f6ff5bc3-aca0-4e4a-8627-e760d0aca78f",\n    "category_name": "Experience"}\n```\n',
            },
            {
                "role": "user",
                "content": json.dumps(full_dict, ensure_ascii=False),
                # "content": "\n    '{\"input_text\": [\"Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?\"],',\n    '\"categories\": [{\"category_id\": \"1711528736036\", \"category_name\": \"The user question is not a single one but a composite of multiple questions.\"}, {\"category_id\": \"1719743471627\", \"category_name\": \"The user question is not composite but a single one.\"}], ',\n    '\"classification_instructions\": [\"\"]}'\n"
            },
        ],
        temperature=0.0,
    )

    response = completion.choices[0].message
    return response.content


def test_classify_question():
    question_text = "Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?"
    categories = {
        1: "The user question is not a single one but a composite of multiple questions.",
        2: "The user question is not composite but a single one.",
    }
    response = classify_question(question_text, categories)
    print(response)

    question_text = QUERY5
    categories = {
        1: "The user question is not a single one but a composite of multiple questions.",
        2: "The user question is not composite but a single one.",
    }
    response = classify_question(question_text, categories)
    print(response)

    question_text = QUERY5
    categories = {
        1: "The question can be answered based on law texts without considering court rulings",
        2: "The question can be answered based on court rulings without considering law texts",
        3: "The question requires knowledge of both law texts and court rulings in order to be answered",
    }
    response = classify_question(question_text, categories)
    print(response)


def get_relevant_paragraphs(question_text, list_of_pars, n=3):
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    full_dict = {"input_text": question_text, "paragraphs": list_of_pars}
    content = json.dumps(full_dict, ensure_ascii=False)
    # print(content)
    completion = client.chat.completions.create(
        model="MaziyarPanahi/Llama-3-8B-Instruct-64k-GGUF",
        # model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        messages=[
            {
                "role": "system",
                "content": f"\n    ### Job Description',\n    You are a legal expert system that analyzes a list of legal excerpts and selects the most relevant {n} based on user input.\n    ### Task\n    Your task is to select the {n} most relevant paragraphs from the list and return their ids in the output. DO NOT ANSWER THE USER QUESTION.\n    ### Format\n    The input text is in the variable input_text. Paragraphs are specified as a list with two fields paragraph_id and paragraph_summary in the variable paragraphs. Further instructions may be included to improve the choice accuracy.\n    ### Constraint\n    DO NOT include anything other than the JSON array in your response.\n   ",
            },
            {
                "role": "user",
                "content": '\n    { "input_text": "Welche Probleme können bei einem Grundstücksstreit bezüglich Eigentumsrechten oder Grenzen auftreten?", "paragraphs": [{"paragraph_id": "1", "paragraph_summary": "Eigentumsrechte in Grundstücksstreitigkeiten"}, {"paragraph_id": "2", "paragraph_summary": "Grenzprobleme und Lösungen"}, {"paragraph_id": "3", "paragraph_summary": "Rechtlicher Rahmen für Grundstückstransaktionen"}, {"paragraph_id": "4", "paragraph_summary": "Gerichtsverfahren im Zusammenhang mit Grundstücksgrenzen"}, {"paragraph_id": "5", "paragraph_summary": "Historische Eigentumsrechte und Grenzen"}]}',
            },
            {"role": "assistant", "content": '\n```json\n["2", "4", "1"]\n```\n'},
            {
                "role": "user",
                "content": '\n    { "input_text": "Was sind die Bedingungen einer Kündigungsklausel im Arbeitsvertrag?", "paragraphs": [{"paragraph_id": "1", "paragraph_summary": "Allgemeine Bedingungen von Arbeitsverträgen"}, {"paragraph_id": "2", "paragraph_summary": "Kündigungsklauseln und -bedingungen"}, {"paragraph_id": "3", "paragraph_summary": "Arbeitnehmerrechte bei Kündigung"}, {"paragraph_id": "4", "paragraph_summary": "Rechtsprechung zu Kündigungen von Arbeitsverträgen"}, {"paragraph_id": "5", "paragraph_summary": "Pflichten des Arbeitgebers bei Kündigungen"}]}',
            },
            {"role": "assistant", "content": '\n```json\n["2", "3"]\n```\n'},
            {
                "role": "user",
                "content": '\n    { "input_text": "Welche Maßnahmen gibt es zur Durchsetzung von geistigen Eigentumsrechten?", "paragraphs": [{"paragraph_id": "1", "paragraph_summary": "Definition von geistigen Eigentumsrechten"}, {"paragraph_id": "2", "paragraph_summary": "Rechtliche Maßnahmen zum Schutz von geistigem Eigentum"}, {"paragraph_id": "3", "paragraph_summary": "Gerichtsverfahren zur Durchsetzung von geistigen Eigentumsrechten"}, {"paragraph_id": "4", "paragraph_summary": "Internationale Abkommen zur Durchsetzung von geistigem Eigentum"}, {"paragraph_id": "5", "paragraph_summary": "Herausforderungen bei der Durchsetzung von geistigen Eigentumsrechten"}]}',
            },
            {
                "role": "assistant",
                "content": '\n```json\n["2", "3", "4", "5"]\n```\n',
            },
            {
                "role": "user",
                "content": '\n    { "input_text": "Welche Umweltvorschriften gibt es zur Entsorgung von Industrieabfällen?", "paragraphs": [{"paragraph_id": "1", "paragraph_summary": "Überblick über Umweltvorschriften"}, {"paragraph_id": "2", "paragraph_summary": "Praktiken im Umgang mit Industrieabfällen"}, {"paragraph_id": "3", "paragraph_summary": "Rechtliche Konsequenzen bei Nichteinhaltung"}, {"paragraph_id": "4", "paragraph_summary": "Fallstudien zu Vorschriften zur Abfallentsorgung"}, {"paragraph_id": "5", "paragraph_summary": "Technologische Lösungen für das Abfallmanagement"}]}',
            },
            {"role": "assistant", "content": '\n```json\n["1", "3"]\n```\n'},
            {
                "role": "user",
                "content": content,
                # "content": "\n    '{\"input_text\": [\"Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?\"],',\n    '\"categories\": [{\"category_id\": \"1711528736036\", \"category_name\": \"The user question is not a single one but a composite of multiple questions.\"}, {\"category_id\": \"1719743471627\", \"category_name\": \"The user question is not composite but a single one.\"}], ',\n    '\"classification_instructions\": [\"\"]}'\n"
            },
        ],
        temperature=0.0,
    )

    response = completion.choices[0].message
    return response.content


def test_get_relevant_paragraphs():
    question_text = "Mein Arbeitgeber zwingt mich, Überstunden ohne Extrazahlung zu leisten. Ist das legal?"
    list_of_pars = [
        {
            "paragraph_id": "1",
            "paragraph_summary": "General employment contract conditions",
        },
        {
            "paragraph_id": "2",
            "paragraph_summary": "Termination clauses and conditions",
        },
        {
            "paragraph_id": "3",
            "paragraph_summary": "Employee rights during termination",
        },
        {
            "paragraph_id": "4",
            "paragraph_summary": "Legal precedents in employment terminations",
        },
        {
            "paragraph_id": "5",
            "paragraph_summary": "Employer obligations in contract terminations",
        },
    ]
    response = get_relevant_paragraphs(question_text, list_of_pars)
    print(response)


def run_final_prompt(full_prompt):
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    completion = client.chat.completions.create(
        model="MaziyarPanahi/Llama-3-8B-Instruct-64k-GGUF",
        # model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        messages=[
            {
                "role": "system",
                "content": f"""
        ### Job Description
        You are a legal expert system called SLANGO that analyzes a user question under the light of a list of legal excerpts and answers the question based on them.
        ### Task
        Please answer the USER inquiry exclusively using the provided reference information, not based on your existing knowledge. 
        The reference information is listed below as paragraphs from law books or summaries of cases. 
        Always cite the book and paragraphs, or the case number and date. Always reply in German.
        """,
            },
            {"role": "user", "content": full_prompt},
        ],
        temperature=0.0,
    )

    response = completion.choices[0].message
    return response.content


if __name__ == "__main__":
    # test_classify_question()
    test_get_relevant_paragraphs()
