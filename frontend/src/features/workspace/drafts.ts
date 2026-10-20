type Draft={sql:string,revision:number};
type Transport=(profile:string,scope:string,sql:string,revision:number)=>Promise<Draft>;
export class DraftSession{
  sql=''; revision=0; savedRevision=0; ready=false; recovery:Draft|null=null;
  private pending:Promise<void>|null=null;
  readonly key:string;
  constructor(readonly profile:string,readonly scope:string,private transport:Transport){this.key=`sql-draft:${profile}:${scope}`}
  get dirty(){return this.revision>this.savedRevision}
  load(draft:Draft){
    this.sql=draft.sql;this.revision=draft.revision;this.savedRevision=draft.revision;this.ready=true;
    try{const saved=JSON.parse(localStorage.getItem(this.key)??'null');if(saved&&saved.sql!==draft.sql&&saved.revision>=draft.revision)this.recovery=saved;}catch{}
  }
  recover(){if(this.recovery){this.edit(this.recovery.sql);this.recovery=null}}
  edit(sql:string){if(sql===this.sql)return;this.sql=sql;this.revision++;localStorage.setItem(this.key,JSON.stringify({sql,revision:this.revision}))}
  async flush(){
    if(this.pending){await this.pending;return}
    if(!this.dirty||!this.ready)return;
    const sql=this.sql, revision=this.revision;
    this.pending=this.transport(this.profile,this.scope,sql,revision).then(()=>{
      this.savedRevision=revision;
      if(!this.dirty)localStorage.removeItem(this.key);
    }).finally(()=>{this.pending=null});
    await this.pending;
  }
  async flushAll(){await this.flush();if(this.dirty)await this.flush()}
}
