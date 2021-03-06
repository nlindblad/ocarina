import inspect
import os
import sys
import sqlite3

import cPickle as pickle

import log
logging = log.getLogger()

from model import model

databaseInstance = {}


def getInstance(filename='results.db', createModel = False):
    global databaseInstance
    fullFilename = os.path.join(os.environ.get('OCARINA_PATH', ''), filename)
    if databaseInstance.get(fullFilename) is not None:
        return databaseInstance.get(fullFilename)
    databaseInstance[fullFilename]= Database(fullFilename, createModel)
    return databaseInstance[fullFilename]


class Database(object):

    def __init__(self, filename, createModel = False):
        try:
            logging.debug('Attempting to open database %s', filename)
            self.conn = sqlite3.connect(filename)
            self.cursor = self.conn.cursor()
            if createModel:
                self._setupNecessary()
        except Exception as e:
            logging.critical('Could not open database %s: %s', filename, e)
            sys.exit(3)

    def _setupNecessary(self):
        global model
        for table in model.iterkeys():
            try:
                logging.debug('Creating table %s if necessary', table)
                self.cursor.execute(model[table])
                self.conn.commit()
            except Exception as e:
                logging.critical('Could not create table %s: %s', table, e)
                sys.exit(4)

    def _executeQuery(self, sql, bindings = list(), return_result = True, commit = True):
        logging.debug('Executing SQL: %s', sql)
        try:
            self.cursor.execute( sql, bindings )
            if commit:
                logging.debug('Commiting to database')
                self.conn.commit()
            if return_result:
                return self.cursor.fetchall()
        except Exception as e:
            logging.critical('Could not execute query: %s', e)
            sys.exit( 7 )

    def _getChord(self):
        """Get the module name of the chord making the database call"""
        frm = inspect.stack()[3]
        mod = inspect.getmodule(frm[0])
        return mod.__name__

    def _constructKeyName(self, key, private = True):
        prefix = self._getChord() + "." if private else ""
        return "%s%s" % (prefix, key)

    def get(self, key, private = True):
        sql = '''SELECT value FROM state WHERE key = ?'''
        result = self._executeQuery(sql, [self._constructKeyName(key, private)], return_result = True)
        if result:
            result = str(result[0][0])
            try:
                return pickle.loads(result)
            except:
                return result
        return None

    def set(self, key, value, private = True):
        value = pickle.dumps(value)
        sql = '''INSERT OR REPLACE INTO state ("key", "value") VALUES (?, ?)'''
        self._executeQuery(
            sql,
            [self._constructKeyName(key, private), value],
            return_result = False,
            commit = True
        )

    def recordExecution(self, start_time, chord_name, execution_time, status,
                        output):
        row = [start_time, chord_name, execution_time, status, output]
        sql = '''INSERT INTO execution VALUES( NULL, ?, ?, ?, ?, ?)'''
        self._executeQuery(sql, row)

    def getExecutions(self, chord_name=None):
        sql = '''SELECT id, time_start, chord_name, execution_time, status, 
                    output FROM execution'''
        where = [' WHERE']
        where_args = []
        if chord_name:
            where.append( 'chord_name=?' )
            where_args.append( chord_name )
        sql += ' '.join( where )
        results = self._executeQuery(sql, where_args, return_result = True)
        return results

    def __del__(self):
        self.conn.close()
