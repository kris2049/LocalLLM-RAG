import pymysql
import pymysql.cursors
from config.config_loader import config

class MySQLDB():
    def __init__(self):
        self.conn = pymysql.connect(
            host=config.database.rag_flow_mysql_host,
            port=config.database.rag_flow_mysql_port,
            user=config.database.rag_flow_mysql_username,
            passwd=config.database.rag_flow_mysql_password,
            db=config.database.rag_flow_mysql_db_name
        )
        self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)


    def select_db(self, sql, params=None):
        """查询"""
        # 检查连接是否断开，如果断开就进行重连
        self.conn.ping(reconnect=True)
        # 使用 execute() 执行sql
        self.cur.execute(sql,params or ())
        # 使用 fetchall() 获取查询结果
        data = self.cur.fetchall()
        return data

    def __del__(self):
        """对象资源被释放时触发，在对象即将被删除时的最后操作"""
        # 关闭游标
        self.cur.close()
        # 关闭数据库连接
        self.conn.close()

    def execute_db(self, sql, params=None):
        """更新/新增/删除"""
        try:
            # 检查连接是否断开，如果断开就进行重连
            self.conn.ping(reconnect=True)
            # 使用 execute() 执行sql
            self.cur.execute(sql, params or ())
            # 提交事务
            self.conn.commit()
            return "插入成功"
        except Exception as e:
            # 回滚所有更改
            self.conn.rollback()
            return f"操作出现错误: {str(e)}"
        
    def execute_many_db(self, sql, params_list=None):
        """批量更新/新增/删除"""
        try:
            self.conn.ping(reconnect=True)

            # 使用executemany进行批量删除
            rows = self.cur.executemany(sql, params_list or ())

            # 提交事务
            self.conn.commit()
            return f"操作成功，影响行数: {rows}"
        except Exception as e:
            self.conn.rollback()
            return f"批量操作失败: {str(e)}"
