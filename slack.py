import json
import requests


def post_to_slack():
    message = [{"type": "section", "text":
        {
            "type": "mrkdwn",
            "text": "한국타이어 매크로\n 뉴일산타이어 - 세션완료입니다. 재 로그인 해주세요."
        }
                }]
    webhook_url = 'https://hooks.slack.com/services/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'
    slack_data = json.dumps({'blocks': message})
    response = requests.post(
        webhook_url, data=slack_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )


post_to_slack()
