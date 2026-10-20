"""Generate and check synthetic, offline packet examples. Never opens a socket."""
from pathlib import Path
import ipaddress
import json
import struct

ROOT=Path(__file__).resolve().parents[1]

def message(kind, body, ipv6=False, vtime=0x48, ttl=1, seq=0x1234):
    addr=ipaddress.ip_address('2001:db8::1' if ipv6 else '10.0.0.1').packed
    header=struct.pack('!BBH',kind,vtime,8+len(addr)+len(body))+addr+struct.pack('!BBH',ttl,0,seq)
    return header+body

def packet(msg,seq=0x1000):
    return struct.pack('!HH',len(msg)+4,seq)+msg

def reltime_to_me_ms(interval):
    # Integer operations from v0.6.8 src/mantissa.c, including quantization.
    unscaled=interval//125*2; b=0
    while unscaled >= (1<<b): b+=1
    if b==0: a=1; b=0
    else:
        b-=1
        if b>15: a=15; b=15
        else:
            if b>=5: a=(interval-(125<<(b-1)))//(125<<(b-5))
            else: a=(interval-(125<<(b-1)))*(1<<(5-b))//125
            b+=a>>4; a&=15
    return (a<<4)|(b&15)

def inspect_olsr(data,ipv6=False):
    if len(data)<4: raise ValueError('short packet')
    length,seq=struct.unpack_from('!HH',data)
    if length!=len(data): raise ValueError('packet length mismatch')
    addrlen=16 if ipv6 else 4; minlen=8+addrlen; pos=4; messages=[]
    while pos<len(data):
        if len(data)-pos<minlen: raise ValueError('short message')
        kind,vtime,size=struct.unpack_from('!BBH',data,pos)
        if size<minlen or size%4 or pos+size>len(data): raise ValueError('invalid message size')
        origin=ipaddress.ip_address(data[pos+4:pos+4+addrlen])
        ttl,hops,mseq=struct.unpack_from('!BBH',data,pos+4+addrlen)
        body=data[pos+minlen:pos+size]
        if kind in (1,201):
            if len(body)<4: raise ValueError('short HELLO')
            off=4
            while off<len(body):
                if len(body)-off<4: raise ValueError('short link block')
                bsize=struct.unpack_from('!H',body,off+2)[0]
                stride=addrlen+(4 if kind==201 else 0)
                if bsize<4 or (bsize-4)%stride or off+bsize>len(body): raise ValueError('invalid link block')
                off+=bsize
        elif kind in (2,202):
            stride=addrlen+(4 if kind==202 else 0)
            if len(body)<4 or (len(body)-4)%stride: raise ValueError('invalid TC')
        elif kind==3 and len(body)%addrlen: raise ValueError('invalid MID')
        elif kind==4 and len(body)%(addrlen*2): raise ValueError('invalid HNA')
        messages.append(dict(type=kind,size=size,originator=str(origin),ttl=ttl,hops=hops,sequence=mseq))
        pos+=size
    return dict(length=length,sequence=seq,ipv6=ipv6,messages=messages)

def ipv4_udp(payload,port):
    src=ipaddress.ip_address('192.0.2.1').packed; dst=ipaddress.ip_address('192.0.2.2').packed
    ip=struct.pack('!BBHHHBBH4s4s',0x45,0,28+len(payload),0,0,64,17,0,src,dst)
    words=struct.unpack('!10H',ip); c=sum(words); c=(c&0xffff)+(c>>16); c=(c&0xffff)+(c>>16)
    ip=ip[:10]+struct.pack('!H',(~c)&0xffff)+ip[12:]
    return ip+struct.pack('!HHHH',port,port,8+len(payload),0)+payload

def main():
    out=ROOT/'examples'; out.mkdir(exist_ok=True)
    assert reltime_to_me_ms(2000)==0x05
    assert reltime_to_me_ms(20000)==0x48
    assert reltime_to_me_ms(300000)==0x2c
    assert (1/16)*(1+(0x2c>>4)/16)*2**(0x2c&15)==288
    rows=[]; pcap=[]
    n4=ipaddress.ip_address('10.0.0.2').packed
    n6=ipaddress.ip_address('2001:db8::2').packed
    quality=bytes.fromhex('ff cc 00 00')
    examples={
        'olsr_lq_hello_ipv4':(packet(message(201,b'\0\0\x05\x03'+b'\x0a\0\0\x0c'+n4+quality)),False),
        'olsr_lq_tc_ipv4':(packet(message(202,b'\0\x07\xff\xff'+n4+quality,vtime=0x08,ttl=255,seq=0x1235),seq=0x1001),False),
        'olsr_hello_ipv4':(packet(message(1,b'\0\0\x05\x03'+b'\x0a\0\0\x08'+n4)),False),
        'olsr_tc_ipv4':(packet(message(2,b'\0\x07\0\0'+n4,ttl=255)),False),
        'olsr_mid_ipv4':(packet(message(3,n4,ttl=255)),False),
        'olsr_hna_ipv4':(packet(message(4,bytes.fromhex('c0 00 02 00 ff ff ff 00'),ttl=255)),False),
        'olsr_lq_hello_ipv6':(packet(message(201,b'\0\0\x05\x03'+b'\x0a\0\0\x18'+n6+quality,True)),True),
        'olsr_lq_tc_ipv6':(packet(message(202,b'\0\x07\xff\xff'+n6+quality,True,ttl=255)),True),
    }
    expected_lengths=[32,28,28,24,20,24,56,52]
    for (name,(data,v6)),expected in zip(examples.items(),expected_lengths):
        assert len(data)==expected,(name,len(data),expected)
        desc=inspect_olsr(data,v6)
        (out/(name+'.bin')).write_bytes(data)
        rows.append(dict(name=name,hex=data.hex(' '),**desc))
        if not v6: pcap.append(ipv4_udp(data,698))
    # Check the exact two byte examples printed in the whitepaper, independently.
    assert examples['olsr_lq_hello_ipv4'][0].hex()=='00201000c948001c0a00000101001234000005030a00000c0a000002ffcc0000'
    assert examples['olsr_lq_tc_ipv4'][0].hex()=='001c1001ca0800180a000001ff0012350007ffff0a000002ffcc0000'
    # Compound packet proves message boundaries need not coincide with UDP boundaries.
    combined=packet(examples['olsr_mid_ipv4'][0][4:]+examples['olsr_hna_ipv4'][0][4:])
    assert len(inspect_olsr(combined)['messages'])==2
    (out/'olsr_mid_and_hna_ipv4.bin').write_bytes(combined)
    rows.append(dict(name='olsr_mid_and_hna_ipv4',hex=combined.hex(' '),**inspect_olsr(combined)))
    pcap.append(ipv4_udp(combined,698))
    failures=0
    for bad in (b'\0', examples['olsr_lq_hello_ipv4'][0][:-1], b'\0\x10\0\0'+b'\xc9\x48\0\x0b'+b'\0'*8):
        try: inspect_olsr(bad)
        except ValueError: failures+=1
    assert failures==3
    rtp=bytes.fromhex('80 00 12 34 00 00 00 a0 11 22 33 44')+bytes([0xff])*160
    assert len(rtp)==172 and struct.unpack_from('!I',rtp,4)[0]==160
    rr=bytes.fromhex('80 c9 00 01 11 22 33 44'); bye=bytes.fromhex('81 cb 00 01 11 22 33 44')
    for data in [rr,bye]: assert (struct.unpack_from('!H',data,2)[0]+1)*4==len(data)
    stun=struct.pack('!HHI',0x0001,0,0x2112a442)+bytes(range(12))
    assert len(stun)==20 and struct.unpack_from('!H',stun,2)[0]==len(stun)-20
    for name,data,port in [('rtp_pcmu',rtp,40000),('rtcp_rr',rr,40001),('rtcp_bye',bye,40001),('stun_binding_request',stun,3478)]:
        (out/(name+'.bin')).write_bytes(data)
        rows.append(dict(name=name,length=len(data),hex=data.hex(' ')))
        pcap.append(ipv4_udp(data,port))
    # LINKTYPE_RAW=101. All addresses and timestamps are synthetic.
    with (out/'synthetic_examples.pcap').open('wb') as f:
        f.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,101))
        for i,data in enumerate(pcap):
            f.write(struct.pack('<IIII',i+1,0,len(data),len(data))); f.write(data)
    (out/'packet_examples.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(valid_examples=len(rows),rejected_malformed_inputs=failures,pcap_packets=len(pcap),live_network_transmission=False)))

if __name__=='__main__': main()
