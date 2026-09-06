from chromadb.utils import embedding_functions

def get_embedding_function():
    """
    Returns default local sentence-transformer embedding function (all-MiniLM-L6-v2)
    which runs offline on CPU/GPU without needing external API keys.
    """
    return embedding_functions.DefaultEmbeddingFunction()
