#@+leo-ver=5-thin
#@+node:2015.20140902161836.3840: * @file pybean.py
#coding: utf-8


#@@language python
#@@tabwidth -4

#@+<<declarations>>
#@+node:2015.20140902161836.3841: ** <<declarations>> (pybean)
import sqlite3
from pkg_resources import parse_version

__version__ = "0.2.1"
__author__ = "Mickael Desfrenes"
__email__ = "desfrenes@gmail.com"
#@-<<declarations>>
#@+others
#@+node:2015.20140902161836.3842: ** class SQLiteWriter
# Yen 2013.04.08, 將 Python2 的 .next() 改為 next(), 以便在 Python 3 中使用

class SQLiteWriter(object):

    """
    In frozen mode (the default), the writer will not alter db schema.
    Just add frozen=False to enable column creation (or just add False
    as second parameter):

    query_writer = SQLiteWriter(":memory:", False)
    """
    #@+others
    #@+node:2015.20140902161836.3843: *3* __init__
    def __init__(self, db_path=":memory:", frozen=True):
        self.db = sqlite3.connect(db_path)
        self.db.isolation_level = None
        self.db.row_factory = sqlite3.Row
        self.frozen = frozen
        self.cursor = self.db.cursor()
        self.cursor.execute("PRAGMA foreign_keys=ON;")
        self.cursor.execute('PRAGMA encoding = "UTF-8";')
        self.cursor.execute('BEGIN;')
    #@+node:2015.20140902161836.3844: *3* __del__
    def __del__(self):
        self.db.close()
    #@+node:2015.20140902161836.3845: *3* replace
    def replace(self, bean):
        keys = []
        values = []
        write_operation = "replace"
        if "id" not in bean.__dict__:
            write_operation = "insert"
            keys.append("id")
            values.append(None)
        self.__create_table(bean.__class__.__name__)
        columns = self.__get_columns(bean.__class__.__name__)
        for key in bean.__dict__:
            keys.append(key)
            if key not in columns:
                self.__create_column(bean.__class__.__name__, key,
                        type(bean.__dict__[key]))
            values.append(bean.__dict__[key])
        sql  = write_operation + " into " + bean.__class__.__name__ + "("
        sql += ",".join(keys) + ") values (" 
        sql += ",".join(["?" for i in keys])  +  ")"
        self.cursor.execute(sql, values)
        if write_operation == "insert":
            bean.id = self.cursor.lastrowid
        return bean.id
    #@+node:2015.20140902161836.3846: *3* __create_column
    def __create_column(self, table, column, sqltype):
        if self.frozen:
            return
        if sqltype in [float, int, bool]:
            sqltype = "NUMERIC"
        else:
            sqltype = "TEXT"
        sql = "alter table " + table + " add " + column + " " + sqltype    
        self.cursor.execute(sql)
    #@+node:2015.20140902161836.3847: *3* __get_columns
    def __get_columns(self, table):
        columns = []
        if self.frozen:
            return columns
        self.cursor.execute("PRAGMA table_info(" + table  + ")")
        for row in self.cursor:
            columns.append(row["name"])
        return columns
    #@+node:2015.20140902161836.3848: *3* __create_table
    def __create_table(self, table):
        if self.frozen:
            return
        sql = "create table if not exists " + table + "(id INTEGER PRIMARY KEY AUTOINCREMENT)"
        self.cursor.execute(sql)
    #@+node:2015.20140902161836.3849: *3* get_rows
    def get_rows(self, table_name, sql = "1", replace = None):
        if replace is None : replace = []
        self.__create_table(table_name)
        sql = "SELECT * FROM " + table_name + " WHERE " + sql
        try:
            self.cursor.execute(sql, replace)
            for row in self.cursor:
                yield row
        except sqlite3.OperationalError:
            return
    #@+node:2015.20140902161836.3850: *3* get_count
    def get_count(self, table_name, sql="1", replace = None):
        if replace is None : replace = []
        self.__create_table(table_name)
        sql = "SELECT count(*) AS cnt FROM " + table_name + " WHERE " + sql
        try:
            self.cursor.execute(sql, replace)
        except sqlite3.OperationalError:
            return 0
        for row in self.cursor:
            return row["cnt"]
    #@+node:2015.20140902161836.3851: *3* delete
    def delete(self, bean):
        self.__create_table(bean.__class__.__name__)
        sql = "delete from " + bean.__class__.__name__ + " where id=?"
        self.cursor.execute(sql,[bean.id])
    #@+node:2015.20140902161836.3852: *3* link
    def link(self, bean_a, bean_b):
        self.replace(bean_a)
        self.replace(bean_b)
        table_a = bean_a.__class__.__name__
        table_b = bean_b.__class__.__name__
        assoc_table = self.__create_assoc_table(table_a, table_b)
        sql = "replace into " + assoc_table + "(" + table_a + "_id," + table_b
        sql += "_id) values(?,?)"
        self.cursor.execute(sql,
                [bean_a.id, bean_b.id])
    #@+node:2015.20140902161836.3853: *3* unlink
    def unlink(self, bean_a, bean_b):
        table_a = bean_a.__class__.__name__
        table_b = bean_b.__class__.__name__
        assoc_table = self.__create_assoc_table(table_a, table_b)
        sql = "delete from " + assoc_table + " where " + table_a
        sql += "_id=? and " + table_b + "_id=?"
        self.cursor.execute(sql,
                [bean_a.id, bean_b.id])
    #@+node:2015.20140902161836.3854: *3* get_linked_rows
    def get_linked_rows(self, bean, table_name):
        bean_table = bean.__class__.__name__
        assoc_table = self.__create_assoc_table(bean_table, table_name)
        sql = "select t.* from " + table_name + " t inner join " + assoc_table 
        sql += " a on a." + table_name + "_id = t.id where a."
        sql += bean_table + "_id=?"
        self.cursor.execute(sql,[bean.id])
        for row in self.cursor:
            yield row
    #@+node:2015.20140902161836.3855: *3* __create_assoc_table
    def __create_assoc_table(self, table_a, table_b):
        assoc_table = "_".join(sorted([table_a, table_b]))
        if not self.frozen:
            sql = "create table if not exists " + assoc_table + "("
            sql+= table_a + "_id NOT NULL REFERENCES " + table_a + "(id) ON DELETE cascade,"
            sql+= table_b + "_id NOT NULL REFERENCES " + table_b + "(id) ON DELETE cascade,"
            sql+= " PRIMARY KEY (" + table_a + "_id," + table_b + "_id));"
            self.cursor.execute(sql)
            # no real support for foreign keys until sqlite3 v3.6.19
            # so here's the hack
            if cmp(parse_version(sqlite3.sqlite_version),parse_version("3.6.19")) < 0:
                sql = "create trigger if not exists fk_" + table_a + "_" + assoc_table
                sql+= " before delete on " + table_a
                sql+= " for each row begin delete from " + assoc_table + " where " + table_a + "_id = OLD.id;end;"
                self.cursor.execute(sql)
                sql = "create trigger if not exists fk_" + table_b + "_" + assoc_table
                sql+= " before delete on " + table_b
                sql+= " for each row begin delete from " + assoc_table + " where " + table_b + "_id = OLD.id;end;"
                self.cursor.execute(sql)
        return assoc_table
    #@+node:2015.20140902161836.3856: *3* delete_all
    def delete_all(self, table_name, sql = "1", replace = None):
        if replace is None : replace = []
        self.__create_table(table_name)
        sql = "DELETE FROM " + table_name + " WHERE " + sql
        try:
            self.cursor.execute(sql, replace)
            return True
        except sqlite3.OperationalError:
            return False
    #@+node:2015.20140902161836.3857: *3* commit
    def commit(self):
        self.db.commit()
    #@-others
#@+node:2015.20140902161836.3858: ** class Store
class Store(object):
    """
    A SQL writer should be passed to the constructor:

    beans_save = Store(SQLiteWriter(":memory"), frozen=False)
    """
    #@+others
    #@+node:2015.20140902161836.3859: *3* __init__
    def __init__(self, SQLWriter):
        self.writer = SQLWriter 
    #@+node:2015.20140902161836.3860: *3* new
    def new(self, table_name):
        new_object = type(table_name,(object,),{})()
        return new_object
    #@+node:2015.20140902161836.3861: *3* save
    def save(self, bean):
        self.writer.replace(bean)
    #@+node:2015.20140902161836.3862: *3* load
    def load(self, table_name, id):
        for row in self.writer.get_rows(table_name, "id=?", [id]):
            return self.row_to_object(table_name, row)
    #@+node:2015.20140902161836.3863: *3* count
    def count(self, table_name, sql = "1", replace=None):
        return self.writer.get_count(table_name, sql, replace if replace is not None else [])
    #@+node:2015.20140902161836.3864: *3* find
    def find(self, table_name, sql = "1", replace=None):
        for row in self.writer.get_rows(table_name, sql, replace if replace is not None else []):
            yield self.row_to_object(table_name, row)
    #@+node:2015.20140902161836.3865: *3* find_one
    def find_one(self, table_name, sql = "1", replace=None):
        try:
            return next(self.find(table_name, sql, replace))
        except StopIteration:
            return None
    #@+node:2015.20140902161836.3866: *3* delete
    def delete(self, bean):
        self.writer.delete(bean)
    #@+node:2015.20140902161836.3867: *3* link
    def link(self, bean_a, bean_b):
        self.writer.link(bean_a, bean_b)
    #@+node:2015.20140902161836.3868: *3* unlink
    def unlink(self, bean_a, bean_b):
        self.writer.unlink(bean_a, bean_b)
    #@+node:2015.20140902161836.3869: *3* get_linked
    def get_linked(self, bean, table_name):
        for row in self.writer.get_linked_rows(bean, table_name):
            yield self.row_to_object(table_name, row)
    #@+node:2015.20140902161836.3870: *3* delete_all
    def delete_all(self, table_name, sql = "1", replace=None):
        return self.writer.delete_all(table_name, sql, replace if replace is not None else [])
    #@+node:2015.20140902161836.3871: *3* row_to_object
    def row_to_object(self, table_name, row):
        new_object = type(table_name,(object,),{})()
        for key in row.keys():
            new_object.__dict__[key] = row[key]
        return new_object
    #@+node:2015.20140902161836.3872: *3* commit
    def commit(self):
        self.writer.commit()
    #@-others
#@-others
#@-leo
