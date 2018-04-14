
import pika
import json
from tradingContext import CFutureMarketData


connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

def callback(ch, method, properties, body):
    _quotation = CFutureMarketData()
    #_dict = body
    #print(body)
    str1  = str(body, 'utf-8').split('|')
    #print(str1[0])
    #print(str1[1])

    _quotation.__dict__ = json.loads(str1[1])
    print (_quotation.instrumentID+','+_quotation.updateTime+','+str(_quotation.lastPrice))

channel.basic_consume(callback,        queue='hello',    no_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

channel.start_consuming()