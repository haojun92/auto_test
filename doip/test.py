from doip import DoIP

def res_check(zcanlib, chn_handle, req_data, res_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i] for i in range(response.response.positive.param_len)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    elif res_list != res_data[1:]:
        test_flg = 0
        print("Response error")

    return test_flg

def read_version(zcanlib, chn_handle, req_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i+2] for i in range(response.response.positive.param_len-2)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    else:
        print("Version is:",''.join(chr(i) for i in res_list))

    return test_flg

def get_response(zcanlib, chn_handle, req_data, project):
    test_flg = 1
    response = uds_req(zcanlib,chn_handle,req_data,project)
    res_list = [response.response.positive.param[i] for i in range(response.response.positive.param_len)]
    if response.status != 0:
        test_flg = 0
        print("No response")
    elif response.type != 1:
        test_flg = 0
        # print("Negative response")
    
    return res_list,test_flg

if __name__ == '__main__':
    doip = DoIP()
    # doip.client.change_session(0x03)
    # # print(doip.client.change_session(0x02).get_payload().hex())
    # # print(doip.client.communication_control(0x03,0x03).get_payload().hex())
    # # print(doip.client.communication_control(0x00,0x03).get_payload().hex())
    # # print(doip.client.request_seed(0x03))
    # # print(doip.client.send_key(0x04,bytes(0x0,0x0,0x0,0x0)))
    # doip.client.unlock_security_access(0x01)
    # doip.client.write_data_by_identifier(0xF190,"0101010101010101010101010101010101")
    # doip.client.read_data_by_identifier(0xF190)
    # doip.client.write_data_by_identifier(0xF190,"0202020202020202020202020202020202")
    # doip.client.read_data_by_identifier(0xF190)
    