from scapy.layers.inet import TCP
from scapy.utils import PcapReader
from os_manager import split_logo, stream_logo, loss_logo, sake_cata, pcap_cata


def handle_tcp(datatext, saketext, protocol, textflag='w'):
    if protocol != 'tcp':
        raise Exception('protocol is not tcp')
    i = 0
    with open(saketext, textflag) as sake:
        with PcapReader(datatext) as scapkts:
            ipsrc, ipdst, prsrc, prdst = None, None, None, None
            # 是否是请求报文。
            beforeflag = True
            for scapkti in scapkts:
                if 'IP' not in scapkti or 'TCP' not in scapkti:
                    continue
                ippkt, tcppkt = scapkti['IP'], scapkti['TCP']
                # 通过IP源地址、目的地址；TCP源端口、目的端口来辨别TCP流。
                # 要求pcap表示的通信是顺序的。
                if (ipsrc, ipdst) != (ippkt.src, ippkt.dst):
                    # 如果TCP流变化，则将当前的流信息写入文件。
                    if ipsrc:
                        sake.write(stream_logo + '\n')
                    ipsrc, ipdst, prsrc, prdst = ippkt.src, ippkt.dst, str(tcppkt.sport), str(tcppkt.dport)
                    i += 1
                    if i == 2:
                        exit(0)
                tcpfields = ['sport', 'dport', 'seq', 'ack', 'dataofs', 'reserved', 'window', 'chksum', 'urgptr']
                result = str(tcppkt.flags) + ':' + split_logo.join([
                    str(getattr(tcppkt, tcpfieldi)) for tcpfieldi in tcpfields
                ])
                if beforeflag:
                    beforeflag = False
                else:
                    sake.write(result + '\n')
                    beforeflag = True


def main(pcaptext, saketext, protocol, textflag='w'):
    handle_tcp(f'{pcap_cata}{pcaptext}.pcap', f'{sake_cata}{saketext}.txt', protocol, textflag)


if __name__ == '__main__':
    main('ftp-upc-active', 'tcp-ftp-upc-active', 'tcp', 'w')
