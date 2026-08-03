import { spawn } from "node:child_process";
type StagerCommand = "validate" | "inspect" | "plan" | "apply";
export type StagerRequest = { command: StagerCommand; manifestPath: string; root?: string; dryRun?: boolean; force?: boolean; };
export function runStager(request: StagerRequest): Promise<Record<string, unknown>> {
  const args=[request.command,request.manifestPath,"--output","json"];
  if(request.root && (request.command==="plan"||request.command==="apply")) args.push("--root",request.root);
  if(request.command==="apply"&&request.dryRun) args.push("--dry-run");
  if(request.command==="apply"&&request.force) args.push("--force");
  return new Promise((resolve,reject)=>{ const child=spawn("stager",args,{stdio:["ignore","pipe","pipe"]}); let out="",err=""; child.stdout.setEncoding("utf8"); child.stderr.setEncoding("utf8"); child.stdout.on("data",c=>out+=c); child.stderr.on("data",c=>err+=c); child.on("error",reject); child.on("close",code=>{ try{const payload=JSON.parse(out); code===0?resolve(payload):reject(new Error(String(payload.error??err??"Stager failed.")));}catch{reject(new Error(err||`Invalid Stager JSON (exit ${code}).`));}}); });
}
