# Security Notes

TitanRAG is designed to avoid committing credentials or private infrastructure details to source control.

## Credential Handling

AWS credentials should be provided through IAM roles, environment variables, or deployment-specific secrets. The repository includes `.env.example` only as a configuration template.

## API Configuration

The Streamlit app should read the backend API URL from an environment variable or Streamlit secrets instead of hard-coding deployment endpoints.

## Data Handling

Uploaded documents are processed through S3-triggered Lambda functions. In production, access to S3, Aurora PostgreSQL, Lambda, and API Gateway should be restricted through least-privilege IAM policies.

## Future Improvements

- Add Cognito or IAM authorization for API Gateway.
- Add request logging and rate limiting.
- Add document-level access control.
- Add encryption checks for S3 and Aurora.