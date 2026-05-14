import os, json, uuid, boto3, urllib.parse

s3 = boto3.client('s3')
rds = boto3.client('rds-data')
bedrock = boto3.client('bedrock-runtime')

DB = os.environ['DB_NAME']
CLUSTER = os.environ['DB_CLUSTER_ARN']
SECRET = os.environ['DB_SECRET_ARN']
EMBED_MODEL = os.environ.get('BEDROCK_EMBED_MODEL', 'amazon.titan-embed-text-v2:0')
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 800))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', 120))

def chunk_text(text: str, size: int, overlap: int):
    """
    Simple character-based chunker with soft word-boundary handling.
    Produces ~size-char chunks, overlapping by ~overlap chars.
    """
    text = " ".join(text.split())  # normalize whitespace
    n = len(text)
    if n == 0:
        return []
    chunks = []
    start = 0
    overlap = min(overlap, max(size // 4, 0))  # keep overlap sane
    while start < n:
        end = min(start + size, n)
        # extend to next space (max +50 chars) to avoid cutting words mid-way
        while end < n and text[end] != ' ' and (end - start) < size + 50:
            end += 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, 0)
        if start >= end:  # safety
            start = end
    return chunks

def embed_one(text: str):
    """
    Bedrock Titan Text Embeddings V2.
    Request: {"inputText": "..."}
    Response contains "embedding": [float,...] (1024 dims if default).
    """
    body = json.dumps({"inputText": text})
    resp = bedrock.invoke_model(modelId=EMBED_MODEL, body=body)
    payload = json.loads(resp['body'].read())
    vec = payload.get("embedding") or payload.get("embeddings")
    # normalize if nested
    if isinstance(vec, list) and len(vec) > 0 and isinstance(vec[0], list):
        vec = vec[0]
    return vec

def insert_batch(rows):
    """
    rows: list of dicts {doc_id, chunk, source, text, embedding(list[float])}
    Uses RDS Data API BatchExecuteStatement in batches of 20.
    """
    sql = (
    "INSERT INTO ra_chunks (doc_id, chunk, source, text, embedding) "
    "VALUES (:doc_id::uuid, :chunk, :source, :text, :embedding::vector)")  
    param_sets = []
    for r in rows:
        param_sets.append([
            {'name': 'doc_id', 'value': {'stringValue': str(r['doc_id'])}},
            {'name': 'chunk', 'value': {'longValue': int(r['chunk'])}},
            {'name': 'source', 'value': {'stringValue': r['source']}},
            {'name': 'text', 'value': {'stringValue': r['text'][:65000]}},
            {'name': 'embedding', 'value': {'stringValue': f"[{','.join(map(str, r['embedding']))}]"}}
        ])
    for i in range(0, len(param_sets), 20):
        rds.batch_execute_statement(
            resourceArn=CLUSTER,
            secretArn=SECRET,
            database=DB,
            sql=sql,
            parameterSets=param_sets[i:i+20]
        )

def lambda_handler(event, context):
    for rec in event.get('Records', []):
        bucket = rec['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(rec['s3']['object']['key'])

        # Expecting txt/ prefix in ra-docs-output-gp
        if bucket != 'ra-docs-output-gp' or not key.startswith('txt/') or not key.lower().endswith('.txt'):
            print(f"Skipping {bucket}/{key}")
            continue

        obj = s3.get_object(Bucket=bucket, Key=key)
        text = obj['Body'].read().decode('utf-8', errors='ignore')
        if not text.strip():
            print("Empty text; skipping.")
            continue

        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"{key}: {len(chunks)} chunks.")
        if not chunks:
            continue

        # Embed first chunk (dimension sanity)
        first_vec = embed_one(chunks[0])
        if not isinstance(first_vec, list):
            print("Embedding failed on first chunk; aborting file.")
            continue
        print(f"Embedding dimension detected: {len(first_vec)}")

        # Embed rest and insert
        doc_id = uuid.uuid4()
        rows = [{
            'doc_id': doc_id,
            'chunk': 0,
            'source': f's3://{bucket}/{key}',
            'text': chunks[0],
            'embedding': first_vec
        }]
        for i in range(1, len(chunks)):
            vec = embed_one(chunks[i])
            if not isinstance(vec, list):
                print(f"Embedding failed on chunk {i}; skipping.")
                continue
            rows.append({
                'doc_id': doc_id,
                'chunk': i,
                'source': f's3://{bucket}/{key}',
                'text': chunks[i],
                'embedding': vec
            })

        insert_batch(rows)
        print(f"Inserted {len(rows)} rows for {key}")

    return {"statusCode": 200, "body": json.dumps("Embedded & stored")}
