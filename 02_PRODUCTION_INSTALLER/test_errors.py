from common.errors import user_message
def test_user_message(): assert 'নিরাপত্তা' in user_message('SEC_SIGNATURE_INVALID')
