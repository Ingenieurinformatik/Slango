from time import time
from sentence_transformers import SentenceTransformer

from .database import get_database


def get_chunks_df():
    # get all chunks that don't have embeddings
    neodb = get_database("milz26")
    query = """
    MATCH (c:Chunk)
    WHERE c.embeddings_e5 IS NULL
    RETURN elementId(c) as id, c.text as text
    """
    chunksdf = neodb.run_query(query)
    return chunksdf


def create_embeddings(chunksdf):
    """Create embeddings for all Chunks in the database"""
    neodb = get_database("milz26")

    print("Loading model...")
    # best german embeddings model: https://www.reddit.com/r/LocalLLaMA/comments/18fsty1/german_language_embedding_model_for_fine_tuned/
    # multilingual-e5-large-instruct
    model = SentenceTransformer(
        'intfloat/multilingual-e5-large-instruct', device="cuda"
    )

    # get the text column as a list
    documents = chunksdf["text"].tolist()

    start_time = time()
    embeddings = model.encode(
        documents, convert_to_tensor=False, normalize_embeddings=True
    )
    end_time = time()
    print(f"Encoding took {end_time - start_time} seconds.")
    # set the embeddings in the dataframe
    chunksdf["embeddings"] = embeddings.tolist()
    print(chunksdf.head())

    # save the embeddings back to the database
    for idx, row in chunksdf.iterrows():
        query = f"""
        MATCH (c:Chunk) WHERE elementId(c) = '{row['id']}'
        SET c.embeddings_e5 = $embeddings
        """
        params = {"embeddings": row["embeddings"]}
        neodb.run_with_params(query, params=params)


if __name__ == "__main__":
    chunksdf = get_chunks_df()
    print(chunksdf)
    create_embeddings(chunksdf)
