"""Authoring source for the offline course; emits reviewable JSON files."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]/'content/chapters'
root.mkdir(parents=True,exist_ok=True)
chapters=[]

def chapter(title,subtitle,lesson,example):
    chapters.append(dict(id=f'{len(chapters)+1:02}',title=title,subtitle=subtitle,lesson=lesson,example_sql=example,problems=[]))

def problem(title,prompt,sql,wrong,hint,syntax,ordered=False,required=None,aliases=False):
    c=chapters[-1]
    p=dict(id=f"{c['id']}-{len(c['problems'])+1:02}",chapter_id=c['id'],title=title,
        prompt=prompt,lesson=c['lesson'],example_sql=c['example_sql'],starter_sql='',
        hints=[hint,syntax],answer_sql=sql,wrong_sql=wrong,equivalent_sql=[],
        output_columns=[],compare_order=ordered,check_aliases=aliases,decimal_places=None,
        required_constructs=required or [])
    c['problems'].append(p)
    return p

chapter('认识数据库','先认识表，再写第一条查询',
        '数据库像一个有组织的资料库。表是一类数据的集合，每行是一条记录，每列是一个字段。主键唯一标识一条记录，客户同名时仍要靠 customer_id 区分。SELECT 选择要看的字段，FROM 指定从哪张表读取。星号 * 表示全部字段。右侧可查看表结构和样例数据。',
        'SELECT * FROM categories;')
problem('第一次认识客户','查询 customers 表的所有字段和全部客户。','SELECT * FROM customers','SELECT * FROM customers LIMIT 10','需要完整的客户表，而不仅是右侧样例的前 10 行。','SELECT * FROM 表名;')
problem('浏览商品目录','查询 products 表的全部商品和所有字段。','SELECT * FROM products','SELECT * FROM categories','先在数据参考中找到“商品”对应的英文表名。','SELECT * FROM products;')
problem('找到客户的身份','只查询全部客户的 customer_id、customer_name，按此顺序输出。','SELECT customer_id, customer_name FROM customers','SELECT customer_name FROM customers','在 SELECT 后列出两个字段，用逗号分开。','SELECT 字段1, 字段2 FROM 表名;')

chapter('基础查询','选择字段，让结果更清晰',
        'SELECT 后可以列出多个字段，输出列顺序与这里一致。AS 为输出列设置易读的别名，不会修改原表。DISTINCT 对所选字段的整行组合去重。字段也能参与计算：数量乘成交单价得到明细金额。',
        'SELECT product_name AS 商品, price AS 标价 FROM products;')
problem('精简商品清单','只输出 product_name、price 两列，查询全部商品。','SELECT product_name,price FROM products','SELECT * FROM products','不需要星号，只列出商品名称与标价。','SELECT product_name, price FROM products;')
problem('给列起中文名字','查询客户姓名和城市，输出别名必须依次为“客户”“城市”。','SELECT customer_name AS 客户,city AS 城市 FROM customers','SELECT customer_name,city FROM customers','AS 设置的是结果列名，中文别名可以用反引号包围。','SELECT 字段 AS 别名, 字段 AS 别名 FROM customers;',aliases=True)
problem('客户来自哪些城市','只输出 city 一列，列出所有不同的城市，包括一条 NULL。使用 DISTINCT。','SELECT DISTINCT city FROM customers','SELECT city FROM customers','多个客户来自同一城市，城市列表需要去重。','SELECT DISTINCT city FROM customers;',required=['Distinct'])
problem('算一算明细金额','查询全部明细，依次输出 item_id、quantity * unit_price 的结果，金额列别名为 line_amount。','SELECT item_id,quantity*unit_price AS line_amount FROM order_items','SELECT item_id,unit_price AS line_amount FROM order_items','成交单价不是整条明细的金额，还要乘数量。','SELECT item_id, quantity * unit_price AS line_amount FROM order_items;',aliases=True)
problem('同城同名也要区分','输出全部客户的 customer_id、customer_name、city 三列。不要按姓名去重。','SELECT customer_id,customer_name,city FROM customers','SELECT DISTINCT customer_name,city FROM customers','客户编号是身份标识，姓名可能相同。','SELECT customer_id, customer_name, city FROM customers;')

chapter('条件筛选','从全部数据中找到目标',
        'WHERE 对每一行判断条件。字符串用单引号包围；AND 要求同时满足，OR 满足任一个即可，混用时用括号明确范围。IN 表示属于给定集合，BETWEEN 包含两端。LIKE 中 % 匹配任意长度文本。NULL 表示缺失，必须用 IS NULL 判断，不能写 = NULL。',
        "SELECT product_name, price FROM products WHERE price >= 100;")
problem('寻找北京客户','输出北京客户的 customer_id、customer_name、city。',"SELECT customer_id,customer_name,city FROM customers WHERE city='北京'","SELECT customer_id,customer_name,city FROM customers WHERE city='上海'",'在客户表上筛选城市字符串。',"WHERE city = '北京'")
problem('筛选高价商品','输出标价严格大于 200 的商品 product_id、product_name、price。','SELECT product_id,product_name,price FROM products WHERE price>200','SELECT product_id,product_name,price FROM products WHERE price<200','严格大于不包括恰好等于边界的值。','WHERE price > 200')
problem('同时满足两个条件','输出数码配件分类（category_id=1）且标价大于 100 的商品，输出全部字段。','SELECT * FROM products WHERE category_id=1 AND price>100','SELECT * FROM products WHERE category_id=1 OR price>100','两个条件都要满足，使用 AND。','WHERE category_id = 1 AND price > 100')
problem('两个城市任意一个','输出上海或北京客户的 customer_id、city；本题要求使用 OR。',"SELECT customer_id,city FROM customers WHERE city='上海' OR city='北京'","SELECT customer_id,city FROM customers WHERE city='上海' AND city='北京'",'一位客户不能同时属于两个城市，这里要任意一个。',"WHERE city='上海' OR city='北京'",required=['Or'])
problem('使用城市列表','输出杭州、广州、成都客户的 customer_id、city；使用 IN。',"SELECT customer_id,city FROM customers WHERE city IN ('杭州','广州','成都')","SELECT customer_id,city FROM customers WHERE city IN ('上海','北京')",'使用集合条件，避免逐个重复写 OR。',"WHERE city IN ('杭州','广州','成都')",required=['In'])
problem('圈定日期区间','查询 2026-03-01 至 2026-03-31（含两端）的订单，输出 order_id、order_date；使用 BETWEEN。',"SELECT order_id,order_date FROM orders WHERE order_date BETWEEN '2026-03-01' AND '2026-03-31'","SELECT order_id,order_date FROM orders WHERE order_date<'2026-03-01'",'order_date 是 DATE 字段，边界直接写固定日期。',"WHERE order_date BETWEEN '2026-03-01' AND '2026-03-31'",required=['Between'])
problem('名字中含有关键词','输出商品名中包含“笔”的商品 product_id、product_name，使用 LIKE。',"SELECT product_id,product_name FROM products WHERE product_name LIKE '%笔%'","SELECT product_id,product_name FROM products WHERE product_name='笔'",'关键词前后可以有其他字符。',"WHERE product_name LIKE '%笔%'",required=['Like'])
problem('找到缺失信息','查询城市缺失的客户，输出 customer_id、customer_name、city。','SELECT customer_id,customer_name,city FROM customers WHERE city IS NULL','SELECT customer_id,customer_name,city FROM customers WHERE city=NULL','NULL 是缺失信息，不能用等号比较。','WHERE city IS NULL')

chapter('排序与截取','让结果按需要排列',
        'ORDER BY ASC 为升序，DESC 为降序，默认是升序。多个排序字段按先后逐层比较。LIMIT 限制返回行数。取前 N 条时要先排序，并使用唯一编号作为并列时的第二排序字段，确保结果稳定。',
        'SELECT product_id, product_name, price FROM products ORDER BY price DESC, product_id ASC LIMIT 3;')
problem('按注册时间排队','输出 customer_id、registered_at，按注册日期升序，日期相同再按客户编号升序。','SELECT customer_id,registered_at FROM customers ORDER BY registered_at,customer_id','SELECT customer_id,registered_at FROM customers ORDER BY registered_at DESC,customer_id', '先写日期排序，再写唯一编号。','ORDER BY registered_at ASC, customer_id ASC',True,['Order'])
problem('最贵的商品在前','输出 product_id、price，按价格降序，同价按商品编号升序。','SELECT product_id,price FROM products ORDER BY price DESC,product_id','SELECT product_id,price FROM products ORDER BY price,product_id','降序使用 DESC。','ORDER BY price DESC, product_id ASC',True,['Order'])
problem('订单按状态和时间排列','输出 order_id、status、order_date，先按 status 升序，再按日期降序，最后订单编号升序。','SELECT order_id,status,order_date FROM orders ORDER BY status ASC,order_date DESC,order_id ASC','SELECT order_id,status,order_date FROM orders ORDER BY order_id','同一状态内按较新的日期在前。','ORDER BY status ASC, order_date DESC, order_id ASC',True,['Order'])
problem('找到前十件高价商品','输出 product_id、product_name、price，价格降序，同价商品编号升序，仅取前 10 件。','SELECT product_id,product_name,price FROM products ORDER BY price DESC,product_id LIMIT 10','SELECT product_id,product_name,price FROM products ORDER BY price,product_id LIMIT 10','LIMIT 放在排序之后。','ORDER BY price DESC, product_id ASC LIMIT 10',True,['Order','Limit'])

chapter('分组统计','从一条条记录中看整体',
        'COUNT(*) 计算行数，COUNT(字段) 不统计 NULL。SUM 求和，AVG 求平均，MIN/MAX 求最小值与最大值。GROUP BY 把相同分组键的行放在一起，每组输出一行。WHERE 在分组前筛行，HAVING 在分组后筛组。非聚合输出字段应符合分组规则。',
        'SELECT category_id, COUNT(*) AS product_count FROM products GROUP BY category_id;')
problem('一共有多少客户','统计客户总人数，输出一列 customer_count。','SELECT COUNT(*) AS customer_count FROM customers','SELECT COUNT(city) AS customer_count FROM customers','城市缺失的客户也要计入总人数。','SELECT COUNT(*) AS customer_count FROM customers;')
problem('一共卖出了多少件','统计全部订单明细的数量之和，包含所有状态订单，输出 total_quantity。','SELECT SUM(quantity) AS total_quantity FROM order_items','SELECT COUNT(*) AS total_quantity FROM order_items','明细行数不等于商品件数。','SELECT SUM(quantity) AS total_quantity FROM order_items;')
problem('平均标价','计算所有商品平均标价，用 ROUND 保留 2 位小数，输出 avg_price。','SELECT ROUND(AVG(price),2) AS avg_price FROM products','SELECT SUM(price) AS avg_price FROM products','先求平均，再对结果保留两位小数。','ROUND(AVG(price), 2)')
problem('价格范围','输出最低和最高商品标价，依次命名 min_price、max_price。','SELECT MIN(price) AS min_price,MAX(price) AS max_price FROM products','SELECT MAX(price) AS min_price,MIN(price) AS max_price FROM products','两个聚合可以写在同一个 SELECT 中。','SELECT MIN(price) AS min_price, MAX(price) AS max_price FROM products;')
problem('各城市的客户数','按 city 分组，依次输出 city、COUNT(*) AS customer_count，包含 NULL 分组，不要求排序。','SELECT city,COUNT(*) AS customer_count FROM customers GROUP BY city','SELECT city,COUNT(city) AS customer_count FROM customers GROUP BY city','NULL 城市也形成一个分组，统计该组人数用 COUNT(*)。','SELECT city, COUNT(*) AS customer_count FROM customers GROUP BY city;',required=['Group'])
problem('订单至少五笔的客户','按 customer_id 统计订单，包含全部订单状态，仅保留订单数至少 5 的客户；输出 customer_id、order_count，不要求排序。','SELECT customer_id,COUNT(*) AS order_count FROM orders GROUP BY customer_id HAVING COUNT(*)>=5','SELECT customer_id,COUNT(*) AS order_count FROM orders GROUP BY customer_id HAVING COUNT(*)>5','对聚合结果筛选应写在 HAVING 中。','GROUP BY customer_id HAVING COUNT(*) >= 5',required=['Having'])

chapter('多表关联','把分散的数据连接起来',
        'JOIN 根据关联键把两张表组合。INNER JOIN 只保留两侧匹配的记录，LEFT JOIN 保留左表全部记录，右侧没有匹配时为 NULL。关联一对多数据会增加行数，这通常是正常现象。用表别名明确同名字段，并用主外键关联，不要用姓名关联。',
        'SELECT o.order_id, c.customer_name FROM orders o INNER JOIN customers c ON o.customer_id=c.customer_id LIMIT 5;')
problem('给订单补上客户姓名','查询全部订单，依次输出 order_id、customer_name，使用 JOIN。','SELECT o.order_id,c.customer_name FROM orders o JOIN customers c ON o.customer_id=c.customer_id','SELECT o.order_id,c.customer_name FROM orders o JOIN customers c ON o.order_id=c.customer_id','订单的 customer_id 指向客户编号。','JOIN customers c ON o.customer_id = c.customer_id',required=['Join'])
problem('商品属于哪个分类','查询所有商品，依次输出 product_id、product_name、category_name。','SELECT p.product_id,p.product_name,c.category_name FROM products p JOIN categories c ON p.category_id=c.category_id','SELECT p.product_id,p.product_name,c.category_name FROM products p JOIN categories c ON p.product_id=c.category_id','分类键是 category_id。','JOIN categories c ON p.category_id = c.category_id',required=['Join'])
problem('展开订单明细','关联 orders、order_items、products，依次输出 order_id、item_id、product_name、quantity，包含所有订单状态。','SELECT o.order_id,i.item_id,p.product_name,i.quantity FROM orders o JOIN order_items i ON o.order_id=i.order_id JOIN products p ON i.product_id=p.product_id','SELECT o.order_id,i.item_id,p.product_name,i.quantity FROM orders o JOIN order_items i ON o.order_id=i.order_id JOIN products p ON i.item_id=p.product_id','先连接订单与明细，再按商品编号连接商品。','orders o JOIN order_items i ON o.order_id=i.order_id JOIN products p ON i.product_id=p.product_id',required=['Join'])
problem('保留没有下单的客户','使用 LEFT JOIN 输出全部客户的 customer_id 和匹配的 order_id。未下单客户的 order_id 应为 NULL。','SELECT c.customer_id,o.order_id FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id','SELECT c.customer_id,o.order_id FROM customers c JOIN orders o ON c.customer_id=o.customer_id','客户放左侧，才能保留没有订单的客户。','customers c LEFT JOIN orders o ON c.customer_id=o.customer_id',required=['Join'])
problem('哪些客户还没下单','使用 LEFT JOIN 找出没有任何订单的客户，输出 customer_id、customer_name。','SELECT c.customer_id,c.customer_name FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id WHERE o.order_id IS NULL','SELECT c.customer_id,c.customer_name FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id WHERE o.order_id IS NOT NULL','用右表非空主键是否为 NULL 判断有没有匹配。','LEFT JOIN orders o ON c.customer_id=o.customer_id WHERE o.order_id IS NULL',required=['Join'])
problem('哪些商品尚未售出','找出没有出现在任何订单明细中的商品，不区分订单状态，输出 product_id、product_name。','SELECT p.product_id,p.product_name FROM products p LEFT JOIN order_items i ON p.product_id=i.product_id WHERE i.item_id IS NULL','SELECT p.product_id,p.product_name FROM products p JOIN order_items i ON p.product_id=i.product_id','从商品表出发，保留未匹配到明细的商品。','LEFT JOIN order_items i ON p.product_id=i.product_id WHERE i.item_id IS NULL',required=['Join'])

chapter('查询进阶','把一个查询作为另一个查询的条件',
        '子查询可以先算出一个值或集合，再供外层查询使用。平均价格等单值结果可放在比较条件中，IN 接受一列结果集合。CASE WHEN 按条件生成新列。NOT IN 遇到 NULL 会影响判断，因此应先确认子查询列是否允许为空。',
        'SELECT product_name, price FROM products WHERE price > (SELECT AVG(price) FROM products);')
problem('高于平均价的商品','使用子查询，输出高于全部商品平均标价的 product_id、price。','SELECT product_id,price FROM products WHERE price>(SELECT AVG(price) FROM products)','SELECT product_id,price FROM products WHERE price<(SELECT AVG(price) FROM products)','内层查询只返回一个平均值。','WHERE price > (SELECT AVG(price) FROM products)',required=['Subquery'])
problem('有已完成订单的客户','使用 IN 子查询，输出至少有一笔 completed 订单的客户 customer_id、customer_name，每个客户只输出一次。',"SELECT customer_id,customer_name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders WHERE status='completed')","SELECT customer_id,customer_name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders WHERE status='pending')",'子查询先找到已完成订单的客户编号集合。',"WHERE customer_id IN (SELECT customer_id FROM orders WHERE status='completed')",required=['In'])
problem('给商品划分价格档位','输出 product_id 和 price_level：price>=200 为“高价”，其他为“常规”。使用 CASE WHEN。',"SELECT product_id,CASE WHEN price>=200 THEN '高价' ELSE '常规' END AS price_level FROM products","SELECT product_id,CASE WHEN price<200 THEN '高价' ELSE '常规' END AS price_level FROM products",'CASE 只生成结果列，不会修改原表。',"CASE WHEN price>=200 THEN '高价' ELSE '常规' END AS price_level",required=['Case'])
problem('换一种方式找未下单客户','使用 NOT IN 子查询，输出未下单的 customer_id、customer_name。orders.customer_id 不允许为 NULL。','SELECT customer_id,customer_name FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders)','SELECT customer_id,customer_name FROM customers WHERE customer_id IN (SELECT customer_id FROM orders)','本题外层保留不在订单客户编号集合中的客户。','WHERE customer_id NOT IN (SELECT customer_id FROM orders)',required=['In'])

chapter('综合练习','用查询回答业务问题',
        '先确定每行输出代表什么，再选择需要的表和关联键。明确业务口径，先筛选再统计，最后排序。销售额按 quantity × unit_price 计算，不要用商品当前标价替代成交价。先从少量字段运行观察，再逐步组合完整查询。',
        "SELECT o.status, SUM(i.quantity*i.unit_price) AS sales FROM orders o JOIN order_items i ON o.order_id=i.order_id GROUP BY o.status;")
problem('各城市的有效订单销售额','关联客户、订单和明细，排除 cancelled 订单，按城市统计销售额。依次输出 city、sales（保留 2 位小数），不要求排序。',"SELECT c.city,ROUND(SUM(i.quantity*i.unit_price),2) AS sales FROM customers c JOIN orders o ON c.customer_id=o.customer_id JOIN order_items i ON o.order_id=i.order_id WHERE o.status<>'cancelled' GROUP BY c.city","SELECT c.city,ROUND(SUM(i.quantity*i.unit_price),2) AS sales FROM customers c JOIN orders o ON c.customer_id=o.customer_id JOIN order_items i ON o.order_id=i.order_id GROUP BY c.city",'先排除取消订单，再按客户所在城市汇总明细金额。',"WHERE o.status <> 'cancelled' GROUP BY c.city")
problem('每月完成了多少笔订单','只统计 completed 订单，按下单月份分组，输出 month（DATE_FORMAT 为 YYYY-MM）、order_count；月份升序。',"SELECT DATE_FORMAT(order_date,'%Y-%m') AS month,COUNT(*) AS order_count FROM orders WHERE status='completed' GROUP BY DATE_FORMAT(order_date,'%Y-%m') ORDER BY month","SELECT DATE_FORMAT(order_date,'%Y-%m') AS month,COUNT(*) AS order_count FROM orders GROUP BY DATE_FORMAT(order_date,'%Y-%m') ORDER BY month",'统计订单数量只需要订单表，不要关联明细导致重复计数。',"SELECT DATE_FORMAT(order_date,'%Y-%m') AS month,COUNT(*) AS order_count ... ORDER BY month",True)
problem('已完成订单的分类销售额','关联分类、商品、明细和订单，只统计 completed 订单，输出 category_name、sales（保留 2 位小数），销售额降序，同额分类名称升序。',"SELECT c.category_name,ROUND(SUM(i.quantity*i.unit_price),2) AS sales FROM categories c JOIN products p ON c.category_id=p.category_id JOIN order_items i ON p.product_id=i.product_id JOIN orders o ON i.order_id=o.order_id WHERE o.status='completed' GROUP BY c.category_id,c.category_name ORDER BY sales DESC,c.category_name ASC","SELECT c.category_name,ROUND(SUM(i.unit_price),2) AS sales FROM categories c JOIN products p ON c.category_id=p.category_id JOIN order_items i ON p.product_id=i.product_id JOIN orders o ON i.order_id=o.order_id WHERE o.status='completed' GROUP BY c.category_id,c.category_name ORDER BY sales DESC,c.category_name ASC",'分类经过商品连接明细，再连接订单限定状态，金额别忘乘数量。','SUM(i.quantity*i.unit_price)，GROUP BY c.category_id,c.category_name',True)
problem('消费最多的五位客户','只统计 completed 订单，按客户汇总成交金额，输出 customer_id、customer_name、sales（保留 2 位小数），销售额降序，同额客户编号升序，取前 5 位。',"SELECT c.customer_id,c.customer_name,ROUND(SUM(i.quantity*i.unit_price),2) AS sales FROM customers c JOIN orders o ON c.customer_id=o.customer_id JOIN order_items i ON o.order_id=i.order_id WHERE o.status='completed' GROUP BY c.customer_id,c.customer_name ORDER BY sales DESC,c.customer_id ASC LIMIT 5","SELECT c.customer_id,c.customer_name,ROUND(SUM(i.quantity*i.unit_price),2) AS sales FROM customers c JOIN orders o ON c.customer_id=o.customer_id JOIN order_items i ON o.order_id=i.order_id WHERE o.status='completed' GROUP BY c.customer_id,c.customer_name ORDER BY sales ASC,c.customer_id ASC LIMIT 5",'客户姓名不能唯一标识客户，按客户编号一起分组。','GROUP BY c.customer_id,c.customer_name ORDER BY sales DESC,c.customer_id ASC LIMIT 5',True)

# Normal hints explain structure; complete solutions belong only to answer reveal.
templates={
    '01-02':'SELECT * FROM <商品表名>;',
    '02-01':'SELECT <商品名称字段>, <标价字段> FROM <商品表名>;',
    '02-03':'SELECT DISTINCT <城市字段> FROM <客户表名>;',
    '02-04':'SELECT <明细编号>, <数量字段> * <成交单价字段> AS <金额别名> FROM <明细表名>;',
    '02-05':'SELECT <客户编号>, <客户姓名>, <城市字段> FROM <客户表名>;',
    '05-01':'SELECT COUNT(*) AS <题目要求的别名> FROM <客户表名>;',
    '05-02':'SELECT SUM(<数量字段>) AS <题目要求的别名> FROM <明细表名>;',
    '05-04':'SELECT MIN(<标价字段>) AS <最低价别名>, MAX(<标价字段>) AS <最高价别名> FROM <商品表名>;',
    '05-05':'SELECT <城市字段>, COUNT(*) AS <人数别名> FROM <客户表名> GROUP BY <城市字段>;',
}
for c in chapters:
    for p in c['problems']:
        if p['id'] in templates:p['hints'][1]='结构参考（请自行替换尖括号中的内容）：'+templates[p['id']]
# These alternatives change table qualification only; they demonstrate acceptance of valid aliases.
for c in chapters:
    for p in c['problems']:
        if not p['required_constructs'] and 'customers' in p['answer_sql'] and 'JOIN' not in p['answer_sql']:
            p['equivalent_sql']=[p['answer_sql'].replace('FROM customers','FROM training.customers')]
        elif len(p['equivalent_sql'])==0 and 'products' in p['answer_sql'] and 'JOIN' not in p['answer_sql']:
            p['equivalent_sql']=[p['answer_sql'].replace('FROM products','FROM training.products')]
    (root/f"{c['id']}.json").write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Generated {sum(len(c["problems"]) for c in chapters)} problems across {len(chapters)} chapters')
