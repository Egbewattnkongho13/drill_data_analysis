from .serve import serve



def lambda_handler(event, context):
    """
    Lambda function handler for serving the silver-level data transfomation service.
    This function is triggered by AWS Lambda and serves the silver-level data transformation service.
    """

    return serve(event, context)