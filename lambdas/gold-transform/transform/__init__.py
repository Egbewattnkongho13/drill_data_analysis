from .serve import serve


def lambda_handler(event, context):
    """
    Lambda function handler for serving the gold-level data transformation service.
    This function is triggered by AWS Lambda and serves the gold-level data transformation service.
    """

    return serve(event, context)
