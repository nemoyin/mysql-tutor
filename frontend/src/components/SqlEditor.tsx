import CodeMirror from '@uiw/react-codemirror';
import {sql,MySQL} from '@codemirror/lang-sql';
const schema={customers:['customer_id','customer_name','city','registered_at'],products:['product_id','product_name','category_id','price'],categories:['category_id','category_name'],orders:['order_id','customer_id','order_date','status'],order_items:['item_id','order_id','product_id','quantity','unit_price']};
export default function SqlEditor({value,onChange,disabled=false,height='205px'}:{value:string,onChange:(s:string)=>void,disabled?:boolean,height?:string}){
  return <CodeMirror value={value} height={height} extensions={[sql({dialect:MySQL,schema})]} onChange={onChange} readOnly={disabled} placeholder="在这里写下你的 SQL，例如 SELECT * FROM customers;" basicSetup={{lineNumbers:true,foldGutter:false,highlightActiveLine:true}} aria-label="SQL 编辑器"/>;
}
