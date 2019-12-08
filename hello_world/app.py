import json
import re
import boto3
import urllib.request
import os
# import requests
from urllib3.exceptions import HTTPError

dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

"""
 sam build
 sam package --template-file template.yaml --output-template-file packaged.yaml --s3-bucket firewood-distribution-checker-for-deploy --profile koty
 sam deploy --template-file packaged.yaml --stack-name firewood-distribution-checker --capabilities CAPABILITY_IAM --profile koty --region ap-northeast-1
"""

SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # ターゲットなるURL
    url = 'http://www.hrr.mlit.go.jp/chikuma/oshirase/karikusa/teikyou_info.html'
    # ページに接続
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
    except HTTPError:
        return {"statusCode": 200, "body": json.dumps({}), }

    # 取得したオブジェクトをhtmlに変換
    find_results = re.search(r'R[元0-9]{1,2}\.\d{1,2}\.\d{1,2}', raw.decode('utf8'))
    if not find_results:
        return {"statusCode": 200, "body": json.dumps({}), }
    date = find_results[0]
    table = dynamodb.Table('firewood-distribution-checker')
    item = table.get_item(
        Key={
            "latest-distribution-date": date,
        }
    )
    if item and item.get('Item'):
        # 更新が無いということなのでメソッド抜ける
        return {"statusCode": 200, "body": json.dumps({}), }

    print('■ 更新があった。')
    # twitterに投稿したい


    print(f'TargetArn={SNS_TOPIC_ARN} ')
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=f'日付：{date}\nhttp://www.hrr.mlit.go.jp/chikuma/oshirase/karikusa/teikyou_info.html',
    )

    # dynamoに直近日付を保存
    table.put_item(
        Item={
            "latest-distribution-date": date,
        }
    )
    return {
        "statusCode": 200,
        "body": json.dumps({
            # "location": ip.text.replace("\n", "")
        }),
    }


if __name__ == '__main__':
    lambda_handler(None, None)
