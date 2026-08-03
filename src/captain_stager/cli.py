import argparse,json,sys
from . import __version__
from .errors import StagerError
from .output import emit_json,print_report
from .service import apply,plan,validate

def build_parser():
    p=argparse.ArgumentParser(prog='stager',description='Prepare target structures from Captain Stager manifests.')
    p.add_argument('--version',action='version',version=__version__); subs=p.add_subparsers(dest='command',required=True)
    for name in ('validate','inspect','plan','apply'):
        c=subs.add_parser(name); c.add_argument('manifest'); c.add_argument('--output',choices=('text','json'),default='text')
        if name in ('plan','apply'): c.add_argument('--root')
        if name=='apply': c.add_argument('--dry-run',action='store_true'); c.add_argument('--force',action='store_true')
    return p

def mdict(m): return {'id':m.id,'name':m.name,'version':m.version,'defaultRoot':m.default_root,'variables':m.variables,'directoryCount':len(m.directories),'fileCount':len(m.files),'sourcePath':str(m.source_path)}
def main(argv=None):
    args=build_parser().parse_args(argv)
    try:
        if args.command=='validate':
            m=validate(args.manifest); payload={'valid':True,'manifest':mdict(m)}; emit_json(payload) if args.output=='json' else print(f"Valid manifest: {m.id} {m.version}"); return 0
        if args.command=='inspect':
            m=validate(args.manifest); payload={**mdict(m),'directories':list(m.directories),'files':[{'path':f.path,'encoding':f.encoding,'overwrite':f.overwrite} for f in m.files]}; emit_json(payload) if args.output=='json' else print(json.dumps(payload,indent=2)); return 0
        if args.command=='plan':
            m,root,ops=plan(args.manifest,args.root); payload={'manifestId':m.id,'root':str(root),'dryRun':True,'succeeded':True,'counts':{'planned':len(ops)},'operations':[{'kind':o.kind,'relativePath':o.relative_path,'targetPath':str(o.target_path),'status':'planned','message':None} for o in ops]}; emit_json(payload) if args.output=='json' else print_report(payload); return 0
        if args.command=='apply':
            report=apply(args.manifest,root_override=args.root,dry_run=args.dry_run,force=args.force); payload=report.to_dict(); emit_json(payload) if args.output=='json' else print_report(payload); return 0 if report.succeeded else 1
    except StagerError as e:
        emit_json({'succeeded':False,'error':str(e)}) if getattr(args,'output','text')=='json' else print(f"stager: {e}",file=sys.stderr); return 2
    return 2
