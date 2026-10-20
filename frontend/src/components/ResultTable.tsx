import type {QueryResult} from '../api/client';
export default function ResultTable({result}:{result:QueryResult|null}){
  if(!result)return <div className="result-empty"><div className="empty-grid">▦</div><strong>让数据回答你的问题</strong><p>写好 SQL，点击「运行 SQL」查看结果。</p></div>;
  return <><div className="result-meta"><span className="success-dot"/>执行成功 · {result.truncated?`显示前 ${result.rows.length} 行`: `${result.rows.length} 行`}<span>{result.elapsed_ms} ms</span></div><div className="table-scroll"><table><thead><tr><th className="row-index">#</th>{result.columns.map((c,i)=><th key={i}>{c.name}<small>{c.kind}</small></th>)}</tr></thead><tbody>{result.rows.map((row,i)=><tr key={i}><td className="row-index">{i+1}</td>{row.map((v,j)=><td key={j}>{v===null?<em className="null-value">NULL</em>:String(v)}</td>)}</tr>)}</tbody></table>{!result.rows.length&&<div className="empty-inline">查询成功，没有符合条件的数据。</div>}</div>{result.truncated&&<p className="note">结果仅展示前 200 行。判题会独立检查完整结果。</p>}</>;
}
