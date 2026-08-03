from pathlib import Path
from .models import ExecutionReport,Operation,OperationResult

def execute_plan(manifest_id:str,root:Path,operations:list[Operation],*,dry_run=False,force=False)->ExecutionReport:
    report=ExecutionReport(manifest_id,str(root),dry_run)
    if not dry_run: root.mkdir(parents=True,exist_ok=True)
    for op in operations:
        try:
            if dry_run:
                report.results.append(OperationResult(op.kind,op.relative_path,str(op.target_path),'planned')); continue
            if op.kind=='mkdir':
                op.target_path.mkdir(parents=True,exist_ok=True); report.results.append(OperationResult('mkdir',op.relative_path,str(op.target_path),'created')); continue
            if op.kind=='write':
                op.target_path.parent.mkdir(parents=True,exist_ok=True)
                if op.target_path.exists() and not (force or op.overwrite):
                    report.results.append(OperationResult('write',op.relative_path,str(op.target_path),'skipped','File already exists.')); continue
                op.target_path.write_text(op.content or '',encoding=op.encoding)
                report.results.append(OperationResult('write',op.relative_path,str(op.target_path),'written')); continue
            report.results.append(OperationResult(op.kind,op.relative_path,str(op.target_path),'failed',f"Unsupported operation: {op.kind}"))
        except OSError as e:
            report.results.append(OperationResult(op.kind,op.relative_path,str(op.target_path),'failed',str(e)))
    return report
