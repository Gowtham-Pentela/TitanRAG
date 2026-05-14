# TitanRAG Architecture

TitanRAG is a serverless Retrieval-Augmented Generation system on AWS.

## System Flow

1. User uploads a PDF document to Amazon S3.
2. S3 triggers a Lambda function.
3. Lambda extracts text from the document.
4. Text is chunked into smaller passages.
5. Amazon Titan Embeddings generate vector embeddings for each chunk.
6. Chunks and embeddings are stored in Aurora PostgreSQL with pgvector.
7. A user submits a question through the Streamlit interface.
8. API Gateway routes the request to a Lambda backend.
9. The backend embeds the user query.
10. Aurora PostgreSQL performs vector similarity search.
11. Retrieved context is passed to a text generation model.
12. The generated answer is returned to the user.

## Design Goals

- Use AWS managed services where possible.
- Keep ingestion event-driven.
- Separate ingestion, retrieval, and user-facing layers.
- Use vector search for semantic retrieval.
- Make the system modular enough for future evaluation and guardrails.