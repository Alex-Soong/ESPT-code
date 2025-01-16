'''
利用pyshark库处理协议报文包。
'''
from pyshark import FileCapture
from pyshark.packet.layers.xml_layer import XmlLayer
from os_manager import split_logo, stream_logo, loss_logo, sake_cata, pcap_cata


def handle_tcp(datatext, saketext, protocol, textflag='w'):
    if protocol != 'tcp':
        raise ValueError('Only TCP protocol is supported.')
    stream_number = 0
    # 假定第一条是响应报文，即第一个报文对缺少请求报文。
    with open(saketext, textflag) as sake:
        while True:
            # 客户端视角的请求端口、响应端口。
            oldprsrc, oldprdst = None, None
            with FileCapture(datatext, keep_packets=False, display_filter=f'tcp.stream eq {stream_number}') as pkts:
                # 一对请求输入报文。
                messpairs = []
                for pkti in pkts:
                    if len(pkti) < 3:
                        continue
                    tcppkt = pkti[2]
                    tcplogos = ['srcport', 'dstport', 'len', 'seq', 'nxtseq', 'ack', 'hdr_len', 'window_size_value',
                                'checksum']
                    tcpminors = [tcppkt.get_field_value(tcplogoi) for tcplogoi in tcplogos]
                    if not oldprdst or not oldprsrc:
                        oldprsrc, oldprdst = tcpminors[1], tcpminors[0]
                    # 标志选取flags还是flags_str？
                    result = tcppkt.get_field_value('flags') + ':' + split_logo.join(tcpminors)
                    # 请求报文。
                    if (oldprsrc, oldprdst) == (tcpminors[0], tcpminors[1]):
                        if messpairs:
                            messpairs.append(loss_logo)
                            sake.write('\n'.join(messpairs) + '\n')
                        messpairs = [result]
                    elif (oldprsrc, oldprdst) == (tcpminors[1], tcpminors[0]):
                        if not messpairs:
                            messpairs.append(loss_logo)
                        messpairs.append(result)
                        sake.write('\n'.join(messpairs) + '\n')
                        messpairs = []
            if not oldprdst or not oldprsrc:
                break
            stream_number += 1
            sake.write(stream_logo + '\n')


def handle_ftp(ftp_pkt):
    '''
    分析FTP协议报文并写入文件。
    :param ftp_pkt: FTP协议数据包。
    :return: 当前报文段解读结果，是否是输入报文。
    '''
    # 当前报文段解读结果，是否是输入报文。
    result, give = 'content', True
    # if 'request' in ftp_pkt.field_names and ftp_pkt.request:
    if 'request_command' in ftp_pkt.field_names:
        result, give = ftp_pkt.get_field_value('request_command') + ':', True
        if 'request_arg' in ftp_pkt.field_names:
            result += ftp_pkt.get_field_value('request_arg')
    # elif 'response' in ftp_pkt.field_names and ftp_pkt.response:
    if 'response_code' in ftp_pkt.field_names:
        result, give = ftp_pkt.get_field_value('response_code') + ':', False
        if 'response_arg' in ftp_pkt.field_names:
            result += ftp_pkt.get_field_value('response_arg')
    return result, give


def handle_smtp(smtp_pkt):
    '''
    分析SMTP协议报文并写入文件。
    :param smtp_pkt: SMTP协议数据包。
    :return: 当前报文段解读结果，是否是输入报文。
    '''
    # 当前报文段解读结果，是否是输入报文。
    result, give = 'content', True
    # 由于参数部分依然可能存在':'，因此读取文件时使用split(':', 1)。
    if smtp_pkt.field_names[0] == 'req' and 'req_command' in smtp_pkt.field_names:
        result, give = smtp_pkt.get_field_value('req_command').upper() + ':', True
        if 'req_parameter' in smtp_pkt.field_names:
            # req_parameter有多个时直接使用.get_field_value('req_parameter')无法全部展示。
            # .get_field_value()返回LayerFieldsContainer对象，其元素是LayerField。
            result += split_logo.join(
                [smtp_fieldi.showname_value
                 for smtp_fieldi in smtp_pkt.get_field_value('req_parameter').all_fields]
            )
    elif smtp_pkt.field_names[0] == 'rsp' and 'response_code' in smtp_pkt.field_names:
        result, give = smtp_pkt.get_field_value('response_code').upper() + ':', False
        if 'rsp_parameter' in smtp_pkt.field_names:
            # rsp_parameter有多个时直接使用.get_field_value('rsp_parameter')无法全部展示。
            result += split_logo.join(
                [smtp_fieldi.showname_value
                 for smtp_fieldi in smtp_pkt.get_field_value('rsp_parameter').all_fields]
            )
    return result, give


def handle_pop(pop_pkt):
    '''
    分析POP协议报文并写入文件。
    :param pop_pkt: POP协议数据包。
    :return: 当前报文段解读结果，是否是输入报文。
    '''
    # 当前报文段解读结果，是否是输入报文。
    result, give = 'content', True
    if pop_pkt.field_names:
        if pop_pkt.field_names[0] == 'request' and 'request_command' in pop_pkt.field_names:
            result, give = pop_pkt.get_field_value('request_command').upper() + ':', True
            if 'request_parameter' in pop_pkt.field_names:
                # request_parameter有多个时直接使用.get_field_value('request_parameter')无法全部展示。
                result += split_logo.join(
                    [pop_fieldi.showname_value
                     for pop_fieldi in pop_pkt.get_field_value('request_parameter').all_fields]
                )
        elif pop_pkt.field_names[0] == 'response' and 'response_indicator' in pop_pkt.field_names:
            result, give = pop_pkt.get_field_value('response_indicator').upper() + ':', False
            if 'response_description' in pop_pkt.field_names:
                # response_description有多个时直接使用.get_field_value('response_description')无法全部展示。
                result += split_logo.join(
                    [pop_fieldi.showname_value
                     for pop_fieldi in pop_pkt.get_field_value('response_description').all_fields]
                )
    return result, give


def handle_lightftp(datatext, saketext, protocol, textflag = 'w'):
    if protocol != 'lightftp':
        raise ValueError('Only LightFTP protocol is supported.')
    # 服务器端口。
    server_port = '9999'
    # 协议的主要字段。
    # majors = [
    #     'CWD', 'EPSV', 'ERPT', 'FEAT', 'LIST', 'MKD', 'NLST', 'PASV', 'PASS', 'PORT', 'QUIT',
    #     'RETR', 'SIZE', 'STOR', 'SYST', 'TYPE', 'USER'
    # ]
    with open(saketext, textflag) as sake:
        stream_number = 0
        flag = True
        while flag:
            with FileCapture(datatext, keep_packets = False, display_filter = f'tcp.stream eq {stream_number}') as caps:
                # 一对输入、输出报文。
                messpairs = []
                flag = False
                for capi in caps:
                    flag = True
                    if len(capi.layers) < 4:
                        continue
                    tcppkt_srcport, tcppkt_dstport = capi[2].srcport, capi[2].dstport
                    if server_port not in (tcppkt_srcport, tcppkt_dstport):
                        if len(messpairs) == 1:
                            messpairs.append(loss_logo)
                        if len(messpairs) == 2:
                            sake.write('\n'.join(messpairs) + '\n')
                        sake.write(stream_logo + '\n')
                        break
                    if capi[3].layer_name != 'DATA':
                        continue
                    lightftppkt = bytes.fromhex(capi[3].data)
                    lftp_letters = lightftppkt.decode('utf-8')
                    # 如果前3个字符是数字，则提取。
                    if lftp_letters[:3].isdigit():
                        space_splits = [lftp_letters[:3], lftp_letters[3:].lstrip('\r\n ')]
                    # 否则先按照' '分割字符串1次。
                    else:
                        space_splits = lftp_letters.split(' ', 1)
                    result = space_splits[0].rstrip('\r\n').upper() + ':'
                    # TODO: 是否需要处理content。
                    # 然后按照'\r\n'分割次要字段。
                    if len(space_splits) > 1:
                        minors = space_splits[1].split('\r\n')
                        result += split_logo.join([minori for minori in minors if minori])
                    # 服务器发过来的响应报文。
                    if tcppkt_srcport == server_port:
                        if not messpairs:
                            messpairs.append(loss_logo)
                        messpairs.append(result)
                        sake.write('\n'.join(messpairs) + '\n')
                        messpairs = []
                    # 客户端发向服务器的请求报文。
                    elif tcppkt_dstport == server_port:
                        # 如果此时messpairs存在内容，说明上一对缺少响应报文。
                        if messpairs:
                            messpairs.append(loss_logo)
                            sake.write('\n'.join(messpairs) + '\n')
                        messpairs = [result]
            stream_number += 1
            sake.write(stream_logo + '\n')


def handle_live555(datatext, saketext, protocol, textflag = 'w'):
    if protocol != 'live555':
        raise ValueError('Only RTSP-Live555 protocol is supported.')
    # 服务器端口。
    server_port = '8554'
    with open(saketext, textflag) as sake:
        stream_number = 0
        # 协议的主要字段。
        flag = True
        while flag:
            with FileCapture(datatext, keep_packets = False, display_filter = f'tcp.stream eq {stream_number}') as caps:
                # 一对输入、输出报文。
                messpairs = []
                flag = False
                for capi in caps:
                    flag = True
                    if len(capi.layers) < 4:
                        continue
                    # 源端口、目的端口。
                    srcport, dstport = str(capi[2].srcport), str(capi[2].dstport)
                    if server_port not in (srcport, dstport):
                        continue
                    rtsppkt: None | XmlLayer = None
                    if capi[3].layer_name == 'rtsp':
                        rtsppkt = capi[3]
                    elif len(capi.layers) > 4 and capi[4].layer_name == 'rtsp':
                        rtsppkt = capi[4]
                    # TODO: 存在部分字段无法获取。
                    logos = rtsppkt.field_names
                    if 'request' in logos:
                        if messpairs:
                            messpairs.append(loss_logo)
                            sake.write('\n'.join(messpairs) + '\n')
                            print(messpairs)
                        result = rtsppkt.get_field_value('method')
                        if not result:
                            result = loss_logo
                        else:
                            result += ':' + split_logo.join([
                                str(rtsppkt.get_field_value(logoi)).rstrip('\\r\\n\r\n')
                                for logoi in logos if logoi not in ('method', 'request')
                            ])
                        messpairs = [result]
                    elif 'response' in logos:
                        if not messpairs:
                            messpairs.append(loss_logo)
                        result = rtsppkt.get_field_value('status')
                        if not result:
                            result = loss_logo
                        else:
                            result += ':' + split_logo.join([
                                str(rtsppkt.get_field_value(logoi)).rstrip('\\r\\n\r\n')
                                for logoi in logos if logoi not in ('status', 'response')
                            ])
                        messpairs.append(result)
                        sake.write('\n'.join(messpairs) + '\n')
                        print(messpairs)
                        messpairs = []
            stream_number += 1
            sake.write(stream_logo + '\n')


def handle(data_text, sake_text, protocol, text_flag = 'w'):
    '''
    分析数据报文并写入文件。
    :param data_text: 数据报文pcap文件名称。
    :param sake_text: 写入目标文件名称。
    :param protocol: 协议名称。
    :param text_flag: 文件的写方式。
    '''
    # 协议处理函数。
    pro_catalog = {
        'ftp': handle_ftp,
        'smtp': handle_smtp,
        'pop': handle_pop
    }
    if protocol not in pro_catalog:
        raise ValueError(f'Protocol {protocol} not supported.')
    with open(sake_text, text_flag) as sake:
        # TCP流编号。
        stream_number = 0
        # 该TCP流中是否含有报文，不能直接使用len()判断 -> 0 packets；默认含有。
        flag = True
        while flag:
            # 只有进入内部的循环才会再次置为True。
            # 初始化输入报文标志为False，约定状态机的输入报文对应请求报文。
            flag, old_give = False, False
            with FileCapture(data_text, keep_packets = False,
                             display_filter = f'tcp.stream eq {stream_number}') as caps:
                for capi in caps:
                    flag = True
                    # 从数据链路层开始算。
                    if len(capi.layers) < 4:
                        continue
                    # 分析最高层的报文（pyshark/packet/layers/xml_layer.py/XmlLayer）。
                    data_pkt = capi[3]
                    # 只有POP协议会将无field_names的报文视作载荷报文。
                    if data_pkt.layer_name != protocol or (protocol != 'pop' and not data_pkt.field_names):
                        continue
                    result, give = pro_catalog[protocol](data_pkt)
                    # 如果返回的give标志与上一次的give标志相同的话，表示两次连续的报文时相同的，中间缺少另一种报文。
                    if give is old_give:
                        sake.write(loss_logo + '\n')
                    old_give = give
                    # 写入.txt文件。
                    sake.write(result.replace('\n', ' ') + '\n')
            # 如果报文流结束时，old_give = True，说明上一个报文是请求报文，缺少响应报文。
            if old_give:
                sake.write(loss_logo + '\n')
            # 应该直接写入txt文件或再考虑其他文件。
            # 先根据主要的标识符确定好基本的SPT，在SPT的基础上，根据每两个相邻状态q1, q2获取报文序列的子集，
            # 确定值之间的关系，此时应该使用到csv文件。
            stream_number += 1
            # 增加流之间的分割行。
            sake.write(stream_logo + '\n')
            print(f'Stream {stream_number - 1} has finished!')


def main(pcaptext, saketext, protocol, text_flag = 'w'):
    if protocol == 'tcp':
        handle_tcp(f'{pcap_cata}{pcaptext}', f'{sake_cata}{saketext}.txt', protocol, text_flag)
    elif protocol == 'lightftp':
        handle_lightftp(f'{pcap_cata}{pcaptext}', f'{sake_cata}{saketext}.txt', protocol, text_flag)
    elif protocol == 'live555':
        handle_live555(f'{pcap_cata}{pcaptext}', f'{sake_cata}{saketext}.txt', protocol, text_flag)
    else:
        handle(f'{pcap_cata}{pcaptext}', f'{sake_cata}{saketext}.txt', protocol, text_flag)


if __name__ == '__main__':
    main('live555-rtsp.pcapng', 'live555-rtsp', 'live555', 'w')
