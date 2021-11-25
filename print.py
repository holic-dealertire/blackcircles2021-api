def lambda_handler(event, context):
    return {'event': str(event), 'context': str(context)}
