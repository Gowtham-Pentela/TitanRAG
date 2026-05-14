import json, os, boto3, base64

sm = boto3.client("sagemaker-runtime", region_name=os.getenv("REGION","us-east-1"))
ENDPOINT = os.getenv("ENDPOINT_NAME")

def _resp(status, body_dict):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":"application/json",
            "Access-Control-Allow-Origin":"*",
            "Access-Control-Allow-Headers":"*",
            "Access-Control-Allow-Methods":"OPTIONS,POST"
        },
        "body": json.dumps(body_dict)
    }

def lambda_handler(event, context):
    try:
        if event.get("isBase64Encoded"):
            body = json.loads(base64.b64decode(event.get("body") or b"{}"))
        else:
            body = json.loads(event.get("body") or "{}")
        question = (body.get("question") or "").strip()
        top_k = body.get("top_k", 3)

        if not question:
            return _resp(400, {"error":"Missing 'question'."})

        payload = json.dumps({"question":question, "top_k": top_k}).encode("utf-8")
        r = sm.invoke_endpoint(
            EndpointName=ENDPOINT,
            ContentType="application/json",
            Body=payload
        )
        out = r["Body"].read()
        try:
            return _resp(200, json.loads(out))
        except Exception:
            return _resp(200, {"raw": out.decode("utf-8","ignore")})

    except Exception as e:
        return _resp(500, {"error":"Gateway error", "detail": str(e)})
