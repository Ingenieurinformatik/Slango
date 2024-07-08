from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .database import get_database


def get_laws_df():
    neodb = get_database("milz26")
    # get all laws
    lawsq = f"""
    MATCH (l:Law) return elementId(l) as id, l.content as content 
    """
    lawsdf = neodb.run_query(lawsq)
    return lawsdf


def get_cases_df(laws=None):
    neodb = get_database("milz26")
    # get all cases connected to mentioned laws
    if laws:
        caseq = f"""
        MATCH (c:Case)-[:REF]->(l:Law) 
        WHERE l.code in {laws}
        return elementId(c) as id, c.content as content 
        """
    else:  # get all cases
        caseq = f"""
        MATCH (c:Case) return elementId(c) as id, c.content as content 
        """
    print(caseq)
    casedf = neodb.run_query(caseq)
    return casedf


def create_chunks(nodesdf, batchsize=100):
    """create chunks from the nodes in the dataframe
    The dataframe should have a column 'content' with the text to be chunked,
    and a column 'id' with the elementId of the node
    """
    assert "content" in nodesdf.columns, "The dataframe must have a column 'content'"
    assert "id" in nodesdf.columns, "The dataframe must have a column 'id'"
    chunk_size = 500
    chunk_overlap = 40
    chunk_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # length_function = len,
        add_start_index=True,
    )

    # iterate over all nodes and create chunks
    chunk_create_queries = []

    def create_chunks_from_row(row):
        parcontent = row["content"] if row["content"] is not None else ""
        chunks = chunk_splitter.split_documents([Document(page_content=parcontent)])
        # print(f"Creating {len(chunks)} chunks for {row['id']}")
        if len(chunks) == 0:
            return
        chunkq = f"""
            MATCH (l) WHERE elementId(l) = '{row["id"]}'
            WITH l
            """
        params = {}
        for n, chunk in enumerate(chunks):
            varid = f"{row['id'][-8:].replace(':', '')}{n}"
            # create the chunk nodes in neo4j
            chunkq += f"""
            CREATE (c{varid}:Chunk)-[:CHUNK_OF]->(l)
            SET c{varid}.text = $chunk_content_{varid}, 
            c{varid}.start_index = {chunk.metadata["start_index"]}, 
            c{varid}.param_chunk_size = {chunk_size}, 
            c{varid}.param_chunk_overlap = {chunk_overlap}
            """
            chunk_content = chunk.page_content if chunk.page_content is not None else ""
            params[f"chunk_content_{varid}"] = chunk_content
        chunk_create_queries.append((chunkq, params))

    # lawsdf.head(200).apply(create_chunks_from_row, axis=1)
    nodesdf.apply(create_chunks_from_row, axis=1)
    print(f"Created {len(chunk_create_queries)} chunk creation queries")

    neodb = get_database("milz26")
    # fuse a batch of queries to avoid multiple transactions
    for i in range(0, len(chunk_create_queries), batchsize):
        print(f"Processing batch {i} to {i+batchsize}")
        batch = chunk_create_queries[i : i + batchsize]
        # this is a hack to fuse multiple queries into one, semicolon does not work
        fused_query = "\nWITH 1 as dummy\n".join([q[0] for q in batch])
        fused_params = {}
        for q in batch:
            fused_params.update(q[1])
        # print(fused_query)
        # print(fused_params)
        neodb.run_with_params(fused_query, params=fused_params)


if __name__ == "__main__":
    # create_chunks()
    # lawsdf = get_laws_df()
    # create_chunks(lawsdf)
    casesdf = get_cases_df(
        laws=[
            "AufenthG 2004",
            "AufenthV",
            "AsylVfG 1992",
            "ArbZG",
            "AEntG 2009",
            "StVG",
        ]
    )
    # casesdf = casesdf.iloc[4600:]
    print(casesdf)
    create_chunks(casesdf, batchsize=5)
