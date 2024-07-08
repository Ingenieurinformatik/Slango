from openai import OpenAI

from .database import get_database


def summarize_case(case_text):
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    completion = client.chat.completions.create(
        # model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        model="MaziyarPanahi/Llama-3-8B-Instruct-64k-GGUF",
        messages=[
            {
                "role": "system",
                "content":
                #  "The following instructions are very important to follow exactly. "
                #  "Fassen Sie den folgenden Fall in einem einzigen Absatz auf Deutsch zusammen und behalten Sie dabei die wichtigsten Punkte bei."
                """The following instructions are very important to follow exactly. You are a helpful professional Sparse Priming Representation (SPR) writer. An SPR is a particular kind of use of language for advanced NLP, NLU, and NLG tasks, particularly useful for the latest generation of Large Language Models (LLMs). You will be given information by the USER which you are to summarize as German SPR with a maximum length of one very short paragraph.
        Instructions:
        - Reply only in German.
        - Do not include any additional sentences or phrases before or after the summary.
        - Ensure the summary is concise.""",
            },
            {"role": "user", "content": case_text},
        ],
        temperature=2.0,
    )

    response = completion.choices[0].message
    return response.content


def fetch_and_summarize_case(case_id):
    # get the case text
    neodb = get_database("milz26")
    query = f"""
    MATCH (c:Case) WHERE elementId(c) = "{case_id}"
    RETURN c.content as content, c.fileNumber as fileNumber, 
    c.type as type, c.date as date, c.summary as summary
    """
    df = neodb.run_query(query)
    case_text = df.iloc[0]["content"]
    summary = df.iloc[0]["summary"]
    case_type = df.iloc[0]["type"]
    case_date = df.iloc[0]["date"]
    case_file_number = df.iloc[0]["fileNumber"]
    if summary:
        print("Already summarized")
    else:
        # summarize the case
        summary = summarize_case(case_text)

        # add the summary to the database
        query = f"""
        MATCH (c:Case) WHERE elementId(c) = "{case_id}"
        SET c.summary = $summary
        """
        neodb.run_with_params(query, params={"summary": summary})
    return summary, case_type, case_date, case_file_number


def test_summarize_case():
    neodb = get_database("milz26")
    blacklist = ["4:e916ef84-b975-460a-a304-bf235608adf8:51933"]
    query = f"""
    MATCH (c:Case) WHERE c.summary IS NULL
    AND NOT elementId(c) in {blacklist}
    RETURN elementId(c) as case_id
    """
    df = neodb.run_query(query)
    for _ix, row in df.iterrows():
        print(f"Summarizing case {row['case_id']}")
        case_id = row["case_id"]
        fetch_and_summarize_case(case_id)


if __name__ == '__main__':
    test_summarize_case()
