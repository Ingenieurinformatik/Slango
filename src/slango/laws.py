from openai import OpenAI

from .database import get_database


def SPR_compress(text):
    if not text or text == "":
        return text
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    completion = client.chat.completions.create(
        model="MaziyarPanahi/Llama-3-8B-Instruct-64k-GGUF",
        # model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        messages=[
            {
                "role": "system",
                "content": """The following instructions are very important to follow exactly. You are a helpful professional Sparse Priming Representation (SPR) writer. An SPR is a particular kind of use of language for advanced NLP, NLU, and NLG tasks, particularly useful for the latest generation of Large Language Models (LLMs). You will be given information by the USER which you are to summarize as German SPR with a maximum length of one very short paragraph.
        Instructions:
        - Reply only in German.
        - Do not include any additional sentences or phrases before or after the summary.
        - Ensure the summary is concise and contained within one very short paragraph.""",
                # "The following instructions are very important to follow exactly. "
                # "You are a helpful professional Sparse Priming Representation (SPR) writer. An SPR is a particular kind of use of language for advanced NLP, NLU, and NLG tasks, particularly useful for the latest generation of Large Language Models (LLMs). "
                # "You will be given information by the USER which you are to summarize as German SPR with max length of one very short paragraph. "
                # "Reply always in German."
            },
            {"role": "user", "content": text},
        ],
        temperature=0.0,
    )

    response = completion.choices[0].message
    return response.content


def compress_book(book_code):
    """compress the laws in a book"""
    neodb = get_database("milz26")
    query = f"""
    MATCH (l:Law) WHERE l.code = "{book_code}"
    RETURN elementId(l) as law_id
    """
    df = neodb.run_query(query)
    sprs = []
    for name, row in df.iterrows():
        spr = compress_law(row["law_id"])
        sprs.append(spr)


def compress_law(law_id):
    neodb = get_database("milz26")
    query = f"""
    MATCH (l:Law) WHERE elementId(l) = "{law_id}"
    RETURN l.content as content, l.spr as spr
    """
    df = neodb.run_query(query)
    spr = df.iloc[0]["spr"]
    content = df.iloc[0]["content"]
    if spr:
        pass
        # print("Already SPR compressed")
    else:
        print(f"Compressing law {law_id}")
        spr = SPR_compress(content)

        # add the summary to the database
        query = f"""
        MATCH (l:Law) WHERE elementId(l) = "{law_id}"
        SET l.spr = $spr
        """
        neodb.run_with_params(query, params={"spr": spr})
    return spr


if __name__ == '__main__':
    # get all laws
    neodb = get_database("milz26")
    query = f"""
    MATCH (l:Law) 
    WHERE l.spr is null
    //WHERE l.code in ["AufenthG 2004", "AufenthV", "AsylVfG 1992", "ArbZG", "AEntG 2009", "StVG"]
    RETURN elementId(l) as law_id, l.code as code
    ORDER BY l.code
    """
    df = neodb.run_query(query)
    for name, row in df.iterrows():
        print(f"Compressing {row['law_id']} from book {row['code']}")
        compress_law(row["law_id"])
