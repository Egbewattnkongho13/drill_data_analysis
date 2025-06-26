from .serve import serve



def lambda_handler(event, context):
    """
    Lambda function handler for serving the ingestion service.
    This function is triggered by AWS Lambda and serves the ingestion service.
    """

    return serve(event, context)