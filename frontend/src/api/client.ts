let token='';
export class ApiError extends Error {constructor(message:string,public details:any=null){super(message)}}
export async function api<T=any>(path:string,body?:unknown,method?:string,keepalive=false):Promise<T>{
  const response=await fetch('/api'+path,{method:method??(body===undefined?'GET':'POST'),headers:{'Content-Type':'application/json','X-Local-Token':token},body:body===undefined?undefined:JSON.stringify(body),keepalive});
  const data=await response.json();
  if(!response.ok)throw new ApiError(data.message??'操作未完成，请重试。',data.details);
  if(path==='/bootstrap')token=data.token;
  return data;
}
export function saveDraft(profile:string,scope:string,sql:string,revision:number,keepalive=false){return api(`/profiles/${profile}/drafts/${scope}`,{sql,revision},'PUT',keepalive)}
export type Profile={id:string,nickname:string,last_scope?:string};
export type Chapter={id:string,title:string,subtitle:string,problems:{id:string,title:string}[]};
export type QueryResult={columns:{name:string,kind:string}[],rows:any[][],total_rows:number|null,truncated:boolean,elapsed_ms:number};
