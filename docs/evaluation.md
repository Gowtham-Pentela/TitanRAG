# Evaluation and Limitations

TitanRAG was designed as a retrieval-augmented generation system where answer quality depends on retrieval quality, chunking strategy, and context construction.

## Evaluation Approach

The system can be evaluated using:

1. Retrieval relevance  
   Check whether the top retrieved chunks contain the information needed to answer the user query.

2. Grounded answer quality  
   Check whether the generated answer is supported by retrieved document context.

3. Failure handling  
   Identify cases where the retrieved context is weak, missing, or unrelated to the question.

## Example Evaluation Flow

1. Upload a PDF document to S3.
2. Run the ingestion pipeline to extract, chunk, embed, and store document chunks.
3. Ask a question through the Streamlit interface.
4. Inspect the retrieved context and generated answer.
5. Verify whether the answer is grounded in the retrieved chunks.

## Known Limitations

- The current version focuses on core RAG workflow rather than advanced reranking.
- The system does not yet include document-level access control.
- The app should add confidence thresholds before answering low-relevance queries.
- Future versions can add reranking, citation formatting, and LLM-as-judge evaluation.