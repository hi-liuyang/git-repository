from HFTickTrading import *
from mock_quotation import *


class CApp:
    _root_dir = 'q:\\csv\\'
    csv_dir = os.listdir(_root_dir)
    _instrumentID = 'ru1805'
    #_dir 以每个交易日为目录名
    for _dir in csv_dir:
        if (_dir >= '20180301' and _dir < '20180425'):


            # 模拟发行情
            mock = CMockTickQuotation()
            mock.root_dir = _root_dir
            #mock.file_fullname = mock.root_dir + _dir + '\\' + mock.instrumentID + ('.csv')
            mock.instrumentID = _instrumentID
            mock.tradeDate = _dir
            t = threading.Thread(target=mock.send, args=(), name='MockThread')
            t.start()
            t.join()
            # mock.send()

            context = CTradingContext(mock.tradeDate,mock.instrumentID)
            runType = context.runType

            print('目前运行环境为:' + runType);
            #strategy = CReferenceDeviationSystem(context)
            strategy = CHFTickTrading(context)
            tradingContract = CHFTickTradingContract(context.instrumentID)

            strategy.initialTradingContract(tradingContract)
            tradingContract.exchangeInstrumentStatus = '2'

            handler = CHFMdHandler(context)
            handler.start_consuming()


