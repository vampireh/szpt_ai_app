#coding=utf-8
# sqlserver的连接
import pymssql
import cx_Oracle
import sys
import time

class Oracle:
    def __init__(self,username,password,tns,encoding):
        self.user = username
        self.pwd = password
        self.tns = tns
        self.encoding = encoding
        self.debugMode = False

    def setDebugMode(self,mode=True):
        self.debugMode=mode

    def __GetConnect(self):
        """
        得到连接信息
        返回: conn.cursor()
        """
        if not self.tns:
            raise(NameError,"没有设置TNS信息")
        self.conn = cx_Oracle.connect(self.user, self.pwd, self.tns, encoding=self.encoding)

        cur = self.conn.cursor()
        if not cur:
            raise(NameError,"连接数据库失败")
        else:
            return cur

    def ExecQuery(self,sql):
        """
        执行查询语句
        返回的是一个包含tuple的list，list的元素是记录行，tuple的元素是每行记录的字段

        """
        cur = self.__GetConnect()
        result=cur.execute(sql)
        resList = result.fetchall()
        # 获取表的列名
        titleList = [i[0] for i in cur.description]
        out=[];
        for row in resList:
            new_row = {}
            for i in range(len(titleList)):
                if row[i] is None:
                    new_row[titleList[i]] = ''
                else:
                    new_row[titleList[i]] = row[i]

            out.append(new_row)
        # 查询完毕后必须关闭连接
        # self.conn.close()
        return out

    def ExecNonQuery(self,sql):
        """
        执行非查询语句

        调用示例：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
        """
        cur = self.__GetConnect()
        cur.execute(sql)
        self.conn.commit()
        # 查询完毕后必须关闭连接
        #self.conn.close()

    def close(self):
        self.conn.close()


class Mssql:
    def __init__(self,host,user,password,database,charset):
        self.host = host
        self.user = user
        self.pwd = password
        self.db = database
        self.charset = charset
        self.debugMode = False

    def setDebugMode(self,mode=True):
        self.debugMode=mode

    def __GetConnect(self):
        """
        得到连接信息
        :return: 返回: conn.cursor()
        """

        if not self.db:
            raise(NameError,"没有设置数据库信息")
        self.conn = pymssql.connect(host=self.host,user=self.user,password=self.pwd,database=self.db,charset=self.charset)

        cur = self.conn.cursor()
        if not cur:
            raise(NameError,"连接数据库失败")
        else:
            return cur

    def SaveByDicList(self,dicList,tableName,pk):
        """
            全量保存数据，存在的更新，不存在的新增
            :param dicList:数据字典列表[{}，{}]
            :param tableName:数据表名称
            :param pk:数据表主键
            :return:结果提示，包括code 1、成功 0、失败,msg 信息, 插入数量、更新数量、报错数量、报错数据行列表
        """
        if(len(dicList)>0):
            rowOne = dicList[0]
        else:
            print("无输入数据")
            return {
                    "code":0,
                    "msg":"无输入数据",
                    "insert_number": 0,
                    "update_number": 0,
                    "error_number": 0,
                    "error_list": 0
                }
        insertRowNumber = 0
        updateRowNumber = 0
        errorList = []
        for data in dicList:
            insert_sql = "INSERT INTO " + tableName + " ( "
            update_sql = "UPDATE " + tableName + " SET "


            for title in rowOne:
                insert_sql += " [" + title + "],"

            #删除最后一个逗号
            insert_sql = insert_sql[:-1]
            insert_sql += " ) VALUES "
            insert_sql += " ( "

            for key in data:
                if type(data[key]) is str:
                    insert_sql += "'" + data[key] + "',"
                    if key != pk:
                        update_sql += " [" + key + "]='"+data[key]+"',"
                else:
                    insert_sql += str(data[key]) + ","
                    if key != pk:
                        update_sql += " [" + key + "]="+str(data[key])+","

            # 删除最后一个逗号
            update_sql = update_sql[:-1]
            if type(data[pk]) is str:
                query_sql = "SELECT " + pk + " FROM " + tableName + " WHERE " + pk + " = '" + data[pk] + "'"
                update_sql += " WHERE " + pk + "='" + data[pk] + "'"
            else:
                query_sql = "SELECT " + pk + " FROM " + tableName + " WHERE " + pk + " = " + data[pk]
                update_sql += " WHERE " + pk + "=" + data[pk]
            insert_sql = insert_sql[:-1]
            insert_sql += ")"
            #print(update_sql)


            try:
                res=self.ExecQuery(query_sql)
                if(len(res)==1):
                    if self.debugMode:print("更新",update_sql)
                    self.ExecNonQuery(update_sql)
                    updateRowNumber += 1
                elif(len(res)>1):
                    errorList.append(
                        {
                            "error_msg": "目标数据库中由重复的pk值:"+ str(len(res)),
                            "data": res
                        }
                    )
                else:
                    if self.debugMode: print("插入", insert_sql)
                    self.ExecNonQuery(insert_sql)
                    insertRowNumber += 1
            except pymssql.IntegrityError as e:
                print("主键重复错误:", str(e), data)
                errorList.append(
                    {
                        "error_msg": "主键重复错误:" + str(e),
                        "data": data
                    }
                )
            except Exception as e:
                print("错误:", str(e), data)
                errorList.append(
                    {
                        "error_msg": "错误:" + str(e),
                        "data": data
                    }
                )

            if self.debugMode:
                out = {
                    "code": 1,
                    "msg": "成功执行",
                    "insert_number": insertRowNumber,
                    "update_number": updateRowNumber,
                    "error_number": len(errorList),
                    "error_list": errorList
                }
            else:
                out = {
                    "code": 1,
                    "msg": "成功执行",
                    "insert_number": insertRowNumber,
                    "update_number": updateRowNumber,
                    "error_number": len(errorList),
                }
        return out

    def InsertByDicList(self,dicList,tableName):
        """
            插入数据，存在的更新，不存在的新增
            :param dicList:数据字典列表[{}，{}]
            :param tableName:数据表名称
            :return:结果提示，包括code 1、成功 0、失败,msg 信息, 插入数量、更新数量、报错数量、报错数据行列表
        """
        if (len(dicList) > 0):
            rowOne = dicList[0]
        else:
            print("无输入数据")
            return {
                "code": 0,
                "msg": "无输入数据",
                "insert_number": 0,
                "error_number": 0,
                "error_list": 0
                }

        insertRowNumber=0
        errorList = []
        for data in dicList:
            sql = "INSERT INTO " + tableName + " ( "
            for title in rowOne:
                sql += " [" + title + "],"
            sql = sql[:-1]
            sql += " ) VALUES "
            sql += " ( "
            for key in data:
                if type(data[key]) is str:
                    sql+="'"+data[key]+"',"
                else:
                    sql+= str(data[key])+","
            sql = sql[:-1]
            sql += ")"

            try:
                self.ExecNonQuery(sql)
                insertRowNumber+=1
            except pymssql.IntegrityError as e:
                print("主键重复:", str(e),sql)
                errorList.append(
                    {
                        "error_msg":"主键重复:",
                        "data":data
                    }
                )
            except Exception as e:
                print("错误:", str(e), sql)
                errorList.append(
                    {
                        "error_msg": "错误:" + str(e),
                        "data": data
                    }
                )

            if  self.debugMode:
                out = {
                        "code": 1,
                        "msg": "成功执行",
                        "insert_number": insertRowNumber,
                        "error_number": len(errorList),
                        "error_list":errorList
                       }
            else:
                out = {
                    "code": 1,
                    "msg": "成功执行",
                    "insert_number": insertRowNumber,
                    "error_number": len(errorList),
                     }
        return out

    def ExecQuery(self,sql):
        """
        执行查询语句
         :return:返回的是一个包含dic的list，list的元素是记录行，dic的元素是每行记录的字段名和内容

        """

        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()
        # 获取表的列名
        titleList = [i[0] for i in cur.description]
        out = [];
        for row in resList:
            new_row = {}
            for i in range(len(titleList)):
                new_row[titleList[i]] = row[i]
            out.append(new_row)
        # 查询完毕后必须关闭连接
        #self.conn.close()
        return out

    def ExecNonQuery(self,sql):
        """
         执行非查询语句
         调用示例：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
         :return:None

        """

        cur = self.__GetConnect()
        result=cur.execute(sql)
        self.conn.commit()
        #self.conn.close()
        return result

    def close(self):
        self.conn.close()