import json
import boto3
from io import BytesIO
from PyPDF2 import PdfReader
import os
import urllib.parse

s3 = boto3.client('s3')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'doc-insight-output-gp')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        # URL-decode key
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        print(f"Processing file: {key} from bucket: {bucket}")
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        pdf_stream = BytesIO(obj['Body'].read())
        
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        output_key = f"txt/{key.rsplit('/',1)[-1].replace('.pdf', '.txt')}"
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=text.encode('utf-8', errors='ignore')

        )
        
        print(f"Saved extracted text to {OUTPUT_BUCKET}/{output_key}")
    
    return {
        'statusCode': 200,
        'body': json.dumps("PDF processing complete!")
    }
