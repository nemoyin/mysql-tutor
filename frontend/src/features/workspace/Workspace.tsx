import {useEffect,useRef,useState} from 'react';
import {Play,Send,Lightbulb,BookOpen,ChevronRight,Code2,Check,Save,RotateCcw} from 'lucide-react';
import {api,saveDraft,ApiError,type Profile,type Chapter,type QueryResult} from '../../api/client';
import {DraftSession} from './drafts';
import SqlEditor from '../../components/SqlEditor';
import ResultTable from '../../components/ResultTable';
import SchemaPanel from '../../components/SchemaPanel';

export default function Workspace({profile,scope,chapters,progress,onNavigate,onProgress,initialSql,onGuard}:{profile:Profile,scope:string,chapters:Chapter[],progress:any,onNavigate:(id:string)=>void,onProgress:()=>void,initialSql?:string,onGuard?:(fn:()=>Promise<void>)=>void}){
 const [problem,setProblem]=useState<any>(null),[sqlText,setSql]=useState(''),[result,setResult]=useState<QueryResult|null>(null),[feedback,setFeedback]=useState<any>(null),[busy,setBusy]=useState(false),[ready,setReady]=useState(false),[saved,setSaved]=useState('正在加载草稿…'),[hints,setHints]=useState<string[]>([]),[answer,setAnswer]=useState(''),[lesson,setLesson]=useState(false),[revision,setRevision]=useState(0),[error,setError]=useState(''),[sample,setSample]=useState<QueryResult|null>(null),[saveName,setSaveName]=useState(''),[saveOpen,setSaveOpen]=useState(false),[switching,setSwitching]=useState(false);
 const session=useRef<DraftSession|null>(null);const generation=useRef(0);const lab=scope==='lab';
 useEffect(()=>{onGuard?.(async()=>{await session.current?.flushAll()});return()=>onGuard?.(async()=>{})},[onGuard]);
 useEffect(()=>{
  const id=++generation.current;setReady(false);setResult(null);setFeedback(null);setHints([]);setAnswer('');setError('');setProblem(null);setSample(null);setLesson(false);
  const current=new DraftSession(profile.id,scope,saveDraft);session.current=current;
  Promise.all([api(`/profiles/${profile.id}/drafts/${scope}`),lab?Promise.resolve(null):api(`/problems/${scope}`)]).then(([draft,p])=>{
   if(generation.current!==id)return;current.load(draft);if(initialSql!==undefined)current.edit(initialSql);setSql(current.sql);setProblem(p);setReady(true);setSaved(current.dirty?'待保存':'已自动保存');setRevision(v=>v+1);
  }).catch(e=>setError(e.message));
  return()=>{generation.current++;void current.flushAll().catch(()=>{});};
 },[profile.id,scope]);
 useEffect(()=>{if(!ready)return;const current=session.current!;const timer=setTimeout(()=>{void current.flush().then(()=>{if(session.current===current)setSaved(current.dirty?'待保存':'已自动保存')}).catch(e=>{if(session.current===current){setSaved('保存失败 · 已保留本机副本');setError(e.message)}})},600);return()=>clearTimeout(timer)},[revision,ready]);
 useEffect(()=>{const leave=()=>{const s=session.current;if(s?.dirty)void saveDraft(s.profile,s.scope,s.sql,s.revision,true).catch(()=>{})};window.addEventListener('pagehide',leave);return()=>window.removeEventListener('pagehide',leave)},[]);
 function edit(value:string){session.current?.edit(value);setSql(value);setSaved('待保存');setRevision(v=>v+1)}
 async function go(id:string){setSwitching(true);try{await session.current?.flushAll();onNavigate(id)}catch(e:any){setError(e.message)}finally{setSwitching(false)}}
 async function execute(submit=false){
  if(busy||!ready)return;setBusy(true);setFeedback(null);setError('');const id=generation.current;
  try{await session.current?.flushAll();const payload={profile_id:profile.id,scope,sql:sqlText};
   const data=await api(submit?`/problems/${scope}/submit`:'/query/run',payload);
   if(generation.current!==id)return;
   if(submit){setFeedback(data);onProgress()}else setResult(data);
  }catch(e:any){if(generation.current===id){setError(e.message);if(e instanceof ApiError&&e.details)setFeedback({status:'error',reason:e.details.original})}}finally{if(generation.current===id)setBusy(false)}
 }
 async function hint(){try{const data=await api(`/problems/${scope}/hint`,{profile_id:profile.id,level:hints.length});setHints(v=>[...v,data.hint])}catch(e:any){setError(e.message)}}
 async function reveal(){if(!confirm('查看参考答案后，本题会记录为参考答案后完成。继续查看？'))return;try{const data=await api(`/problems/${scope}/answer`,{profile_id:profile.id});setAnswer(data.sql);onProgress()}catch(e:any){setError(e.message)}}
 const all=chapters.flatMap(c=>c.problems),index=all.findIndex(p=>p.id===scope),chapter=chapters.find(c=>c.problems.some(p=>p.id===scope));
 return <div className={'workspace '+(lab?'is-lab':'')}>
 {!lab&&<aside className="course-rail"><div className="rail-heading">查询分析课程 <small>8 个章节</small></div>{chapters.map(c=><details key={c.id} open={c.id===chapter?.id}><summary><span>{c.id}</span>{c.title}<ChevronRight size={13}/></summary><div>{c.problems.map(p=><button disabled={switching} key={p.id} onClick={()=>go(p.id)} className={p.id===scope?'selected':''}><span className={'lesson-dot '+(progress[p.id]?.mode?'done':'')}>{progress[p.id]?.mode?<Check size={10}/>:null}</span>{p.title}</button>)}</div></details>)}</aside>}
 <div className="workspace-main"><div className="task-heading"><div className="eyebrow">{lab?'YOUR SQL PLAYGROUND':`CHAPTER ${chapter?.id??''} · ${chapter?.title??''}`}</div><h1>{lab?'自由实验室':problem?.title??'正在加载…'}</h1><p>{lab?'从一个问题出发，自由探索这套电商数据。':problem?.prompt}</p>{!lab&&<div className="task-tools"><button onClick={()=>setLesson(!lesson)} className={lesson?'active':''}><BookOpen size={14}/>{lesson?'收起知识讲解':'知识讲解与示例'}</button><span>练习 {index+1} / 40</span></div>}</div>
 {lesson&&problem&&<section className="lesson-card"><h3>先理解，再动手</h3><p>{problem.lesson}</p><pre>{problem.example_sql}</pre><button className="text-button" onClick={async()=>{try{setSample(await api('/query/run',{profile_id:profile.id,scope,sql:problem.example_sql}))}catch(e:any){setError(e.message)}}}><Play size={12}/>运行示例（保留你的草稿）</button>{sample&&<ResultTable result={sample}/>}</section>}
 {session.current?.recovery&&<div className="notice">发现未保存的本机草稿。<button onClick={()=>{session.current!.recover();setSql(session.current!.sql);setRevision(v=>v+1)}}>恢复草稿</button></div>}
 <section className="editor-card"><div className="editor-title"><span><Code2 size={16}/>SQL 编辑器 <small>MySQL</small></span><span className="save-state"><Check size={12}/>{saved}</span></div><SqlEditor value={sqlText} onChange={edit} disabled={!ready||switching} height={lab?'275px':'205px'}/><div className="editor-actions"><span>只读查询 · 可以放心练习</span><div>{lab&&<button disabled={!ready} onClick={()=>setSaveOpen(true)}><Save size={14}/>保存 SQL</button>}<button disabled={!ready||busy||!sqlText.trim()} onClick={()=>execute(false)}><Play size={14}/>{busy?'执行中…':'运行 SQL'}</button>{!lab&&<button className="primary" disabled={!ready||busy||!sqlText.trim()} onClick={()=>execute(true)}><Send size={14}/>提交判题</button>}</div></div></section>
 {error&&<div className="feedback error"><strong>需要检查一下</strong><p>{error}</p></div>}{feedback&&<div className={'feedback '+feedback.status}><strong>{feedback.status==='passed'?'✓ 回答正确':feedback.status==='incorrect'?'再检查一下':feedback.status==='ungraded'?'暂未完成判题':'MySQL 原始信息'}</strong><pre>{feedback.reason}</pre>{feedback.status==='passed'&&index+1<all.length&&<button onClick={()=>go(all[index+1].id)}>下一道练习 <ChevronRight size={14}/></button>}</div>}
 {!lab&&<div className="hint-row"><span><Lightbulb size={15}/>卡住了？一步一步找到思路</span><div><button disabled={hints.length>=2} onClick={hint}>{hints.length>=2?'已显示全部提示':`查看提示 ${hints.length+1}`}</button><button onClick={reveal}>参考答案</button></div></div>}{hints.map((h,i)=><div className="hint-card" key={i}><b>提示 {i+1}</b><p>{h}</p></div>)}{answer&&<div className="answer-card"><b>参考答案 · 试着理解每一部分</b><pre>{answer}</pre><button onClick={()=>{if(!sqlText||confirm('用参考答案替换当前编辑内容？'))edit(answer)}}>放入编辑器</button></div>}
 <section className="results-card"><div className="panel-title">查询结果<span className="tiny-badge">RESULTS</span>{result&&<button className="icon-button" title="清空展示结果" onClick={()=>setResult(null)}><RotateCcw size={13}/></button>}</div><ResultTable result={result}/></section>
 </div><SchemaPanel/>{saveOpen&&<div className="modal-backdrop"><form className="modal" onSubmit={async e=>{e.preventDefault();try{await api(`/profiles/${profile.id}/saved`,{name:saveName,sql:sqlText});setSaveOpen(false);setSaveName('');setSaved('SQL 已命名保存')}catch(e:any){setError(e.message)}}}><h2>保存这条查询</h2><label>给查询起个名字<input value={saveName} onChange={e=>setSaveName(e.target.value)} required maxLength={60} autoFocus/></label><div className="modal-actions"><button type="button" onClick={()=>setSaveOpen(false)}>取消</button><button className="primary">保存</button></div></form></div>}
 </div>
}
