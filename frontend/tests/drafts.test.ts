import {describe,it,expect} from 'vitest';

describe('DraftSession',()=>{
  it('keeps profile and scope drafts isolated and saves latest edit',async()=>{
    const {DraftSession}=await import('../src/features/workspace/drafts');
    const writes:any[]=[];
    const transport=async(p:string,s:string,sql:string,r:number)=>{writes.push({p,s,sql,r});return {sql,revision:r}};
    const a=new DraftSession('a','01-01',transport);
    const b=new DraftSession('b','01-01',transport);
    a.load({sql:'SELECT 1',revision:1}); b.load({sql:'SELECT 2',revision:1});
    a.edit('SELECT 3'); a.edit('SELECT 4');
    await a.flush();
    expect(writes).toEqual([{p:'a',s:'01-01',sql:'SELECT 4',r:3}]);
    expect(b.sql).toBe('SELECT 2');
  });
  it('retains recovery copy when saving fails',async()=>{
    const {DraftSession}=await import('../src/features/workspace/drafts');
    const a=new DraftSession('a','02-01',async()=>{throw Error('offline')});
    a.load({sql:'',revision:0});a.edit('SELECT 7');
    await expect(a.flush()).rejects.toThrow('offline');
    const recovery=JSON.parse(localStorage.getItem(a.key)!);
    expect(recovery.sql).toBe('SELECT 7');
  });
  it('does not mark a newer edit saved when an earlier save finishes',async()=>{
    const {DraftSession}=await import('../src/features/workspace/drafts');
    let finish!:(v:any)=>void;
    const a=new DraftSession('a','03-01',async(_p:string,_s:string,sql:string,r:number)=>new Promise(resolve=>{finish=()=>resolve({sql,revision:r})}));
    a.load({sql:'',revision:0});a.edit('SELECT 1');
    const pending=a.flush();a.edit('SELECT 2');finish({});await pending;
    expect(a.dirty).toBe(true);
    expect(a.sql).toBe('SELECT 2');
  });
});
