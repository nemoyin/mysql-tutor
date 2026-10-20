"""Build the checked-in deterministic teaching dataset; not run on learner startup."""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1] / 'backend/trainer/dataset'
lines = []
def insert(table, rows):
    def literal(value):
        if value is None: return 'NULL'
        if isinstance(value, (int, Decimal)): return str(value)
        return "'" + str(value).replace("'", "''") + "'"
    lines.append(f'INSERT IGNORE INTO {table} VALUES ' + ',\n'.join('(' + ','.join(map(literal, r)) + ')' for r in rows) + ';')

insert('categories', [(i+1,n) for i,n in enumerate(['数码配件','生活家居','文具办公','运动户外','食品饮料','图书阅读'])])
names = ['林晓','陈晨','王敏','李明','张悦','赵磊','刘洋','周宁','吴桐','郑佳','孙浩','徐静','朱琳','马超','胡杨','郭欣','何川','高原','罗晴','梁宇','宋雨','唐心','许安','韩梅','冯卓','邓凯','曹雪','彭博','曾乐','林晓']
insert('customers', [(i+1,n, None if i==28 else ['上海','北京','杭州','广州','成都'][i%5], date(2026,1,1)+timedelta(days=i*3)) for i,n in enumerate(names)])
product_names=['便携充电线','桌面收纳盒','方格笔记本','运动水杯','挂耳咖啡','SQL入门指南','无线鼠标','棉麻桌布','中性笔套装','瑜伽拉力带','坚果礼盒','数据分析实战','手机支架','香氛蜡烛','文件夹','露营灯','乌龙茶','阅读手账','蓝牙耳机','保温杯','便利贴','跳绳','黑巧克力','Python学习笔记','移动电源','靠垫','订书机','速干毛巾','燕麦片','统计学入门','键盘清洁刷','折叠衣架','书签套装','登山扣','蜂蜜','商业分析案例','相机包','陶瓷花瓶','绘图尺','运动护腕']
insert('products',[(i+1,n,i%6+1,Decimal('19.90')+Decimal(i*10)) for i,n in enumerate(product_names)])
insert('orders',[(i,(i-1)%24+1,date(2026,1,1)+timedelta(days=(i*7)%181),'cancelled' if i%10==0 else ('pending' if i%7==0 else 'completed')) for i in range(1,121)])
items=[]
for order in range(1,121):
    for j in range(2 if order<=60 else 3):
        k=len(items)
        pid=k%36+1
        q=k%3+1
        price=Decimal('19.90')+Decimal((pid-1)*10)
        if order==1: q,price = (2,Decimal('19.90')) if j==0 else (1,Decimal('40.00'))
        items.append((k+1,order,pid,q,price))
insert('order_items',items)
(root/'seed.sql').write_text('\n'.join(lines),encoding='utf-8')
definitions={
'customers':('客户','客户档案；同名不代表同一个人。',[('customer_id','INT','客户编号（主键）'),('customer_name','VARCHAR','客户姓名'),('city','VARCHAR','所在城市，可为空'),('registered_at','DATE','注册日期')]),
'categories':('商品分类','商品所属分类。',[('category_id','INT','分类编号（主键）'),('category_name','VARCHAR','分类名称')]),
'products':('商品','商品当前标价，与历史成交价可能不同。',[('product_id','INT','商品编号（主键）'),('product_name','VARCHAR','商品名称'),('category_id','INT','分类编号'),('price','DECIMAL(10,2)','当前标价')]),
'orders':('订单','每行一笔订单；completed 已完成，pending 待处理，cancelled 已取消。',[('order_id','INT','订单编号（主键）'),('customer_id','INT','客户编号'),('order_date','DATE','下单日期'),('status','VARCHAR','订单状态')]),
'order_items':('订单明细','每行一种购买商品；销售额 = quantity × unit_price。',[('item_id','INT','明细编号（主键）'),('order_id','INT','订单编号'),('product_id','INT','商品编号'),('quantity','INT','购买数量'),('unit_price','DECIMAL(10,2)','成交单价')])}
relations={'products':[('category_id','categories','category_id')],'orders':[('customer_id','customers','customer_id')],'order_items':[('order_id','orders','order_id'),('product_id','products','product_id')]}
catalog=[dict(name=t,label=d[0],description=d[1],columns=[dict(name=n,mysql_type=k,nullable=n=='city',description=s) for n,k,s in d[2]],relations=[dict(column=c,target_table=tt,target_column=tc) for c,tt,tc in relations.get(t,[])]) for t,d in definitions.items()]
(root/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
