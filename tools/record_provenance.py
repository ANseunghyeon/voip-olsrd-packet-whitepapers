"""Record evidence hashes without copying the upstream source tree."""
from pathlib import Path
import hashlib,json,argparse,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=argparse.ArgumentParser(); a.add_argument('olsrd_source',type=Path); a.add_argument('--archive',type=Path); args=a.parse_args()
    filelist=['src/olsr_protocol.h','src/olsr_cfg.h','src/lq_packet.c','src/lq_packet.h','src/lq_plugin.c','src/lq_plugin_default_ff.c','src/net_olsr.c','src/parser.c','src/mantissa.c','src/build_msg.c','src/generate_msg.c','src/gateway.c','src/gateway.h','src/olsr.c','src/process_package.c','src/cfgparser/olsrd_conf.c','src/olsr_types.h','lib/secure/src/olsrd_secure.c','lib/secure/src/secure_messages.h','lib/nameservice/src/nameservice.c','lib/nameservice/src/nameservice.h','lib/nameservice/src/nameservice_msg.h','lib/mdns/src/mdns.c','lib/mdns/src/RouterElection.c','lib/mdns/src/RouterElection.h','lib/p2pd/src/p2pd.c','lib/pud/wireformat/include/OlsrdPudWireFormat/wireFormat.h','lib/pud/src/configuration.h','lib/pud/src/gpsConversion.c','lib/bmf/src/Packet.h','lib/bmf/src/Bmf.h','lib/txtinfo/src/olsrd_plugin.c','lib/jsoninfo/src/olsrd_plugin.c','lib/httpinfo/src/olsrd_httpinfo.c','lib/pgraph/src/olsrd_pgraph.c','src/ipc_frontend.h']
    data={'retrieved_date':'2026-10-20','timezone':'Asia/Seoul','olsrd':{'repository':'https://github.com/OLSR/olsrd','tag':'v0.6.8','commit':'51ac86b22ee2bdb1077c889859ad3ca5a39aa079','archive_url':'https://codeload.github.com/OLSR/olsrd/zip/refs/tags/v0.6.8','files_sha256':{x:sha(args.olsrd_source/x) for x in filelist}},'iana':[],'verification':{'method':'static source inspection and synthetic offline examples','live_daemon_test':False}}
    if args.archive: data['olsrd']['downloaded_archive_sha256']=sha(args.archive)
    for path in sorted((ROOT/'sources').glob('*.xml')):
        xml=ET.parse(path).getroot(); ns={'i':'http://www.iana.org/assignments'}
        data['iana'].append({'file':path.name,'url':'https://www.iana.org/assignments/'+path.stem+'/'+path.name,'last_updated':xml.findtext('i:updated',namespaces=ns),'sha256':sha(path)})
    data['itu']=json.loads((ROOT/'sources'/'h323_message_inventory.json').read_text(encoding='utf-8'))['sources']
    (ROOT/'sources'/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Hashed',len(filelist),'upstream source files and',len(data['iana']),'IANA snapshots')
if __name__=='__main__': main()
