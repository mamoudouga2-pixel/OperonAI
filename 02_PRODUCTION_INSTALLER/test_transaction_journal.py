from installer_engine.journal import TransactionJournal
def test_journal(tmp_path):
    j=TransactionJournal(tmp_path/'j.jsonl'); j.append('TRANSACTION_STARTED',component_id='x'); assert j.read()[0]['event']=='TRANSACTION_STARTED'
