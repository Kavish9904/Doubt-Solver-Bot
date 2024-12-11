from src.helper import load_pdf, text_split, download_hugging_face_embeddings
from langchain.vectorstores import Pinecone as LangchainPinecone
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_CLOUD = os.environ.get('PINECONE_CLOUD', 'aws')  # Default to 'aws' if not specified
PINECONE_REGION = os.environ.get('PINECONE_REGION')  # e.g., 'us-west-2'

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

extracted_data = load_pdf("data/")
text_chunks = text_split(extracted_data)
embeddings = download_hugging_face_embeddings()

# Pinecone index creation and data insertion
index_name = "chatbot"

# Check if index exists, create if it doesn't
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,  # dimension of all-MiniLM-L6-v2 embeddings
        metric="cosine",
        spec=ServerlessSpec(
            cloud=PINECONE_CLOUD,
            region=PINECONE_REGION
        )
    )

# Get the index
index = pc.Index(index_name)

# Debug: Check if text_chunks exists and is not empty
if 'text_chunks' not in globals():
    print("Error: text_chunks is not defined. Make sure you've run the previous cells.")
elif not text_chunks:
    print("Error: text_chunks is empty. Check if the PDF loading was successful.")
else:
    print(f"Number of text chunks: {len(text_chunks)}")

    # Create embeddings for text chunks
    texts = [t.page_content for t in text_chunks]
    print(f"Number of texts: {len(texts)}")

    embeddings_list = embeddings.embed_documents(texts)
    print(f"Number of embeddings: {len(embeddings_list)}")

    # Prepare data for upsert
    vectors = [
        (str(i), embedding, {"text": text})
        for i, (embedding, text) in enumerate(zip(embeddings_list, texts))
    ]
    print(f"Number of vectors: {len(vectors)}")

    # Batch upsert to Pinecone
    batch_size = 100  # You can adjust this value
    for i in tqdm(range(0, len(vectors), batch_size)):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)