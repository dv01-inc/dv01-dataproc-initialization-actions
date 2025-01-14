#!/usr/bin/python

import pyspark
import random
import string
from xml.dom import minidom

# Constants that must match the constants in cloud-sql-proxy.sh
METASTORE_DB = 'hive_metastore'
HIVE_USER = 'hive'
HIVE_USER_PASSWORD = 'hive-password'

dom = minidom.parse('/etc/hive/conf/hive-site.xml')
element = dom.getElementsByTagName('property')
name=''
value=''
for property in dom.getElementsByTagName("property"):
    name  = property.getElementsByTagName("name")[0].childNodes[0].data
    value = property.getElementsByTagName("value")[0].childNodes[0].data
    if name=="javax.jdo.option.ConnectionPassword":
       break
if value != 'none':
    HIVE_USER_PASSWORD=value

sc = pyspark.SparkContext()
sqlContext = pyspark.sql.HiveContext(sc)

# Find available table name.
table_names = sqlContext.tableNames()
test_table_name = None
while not test_table_name or test_table_name in table_names:
  test_table_name = 'table_' + ''.join(
      [random.choice(string.ascii_lowercase) for x in range(4)])

# Create table.
sqlContext.range(10).write.saveAsTable(test_table_name)

# Read table metadata from Cloud SQL proxy.
tables = sqlContext.read.jdbc(
    'jdbc:mysql:///{}?user={}&password={}'.format(METASTORE_DB, HIVE_USER,
                                                  HIVE_USER_PASSWORD), 'TBLS')
test_table = tables.where(tables.TBL_NAME == test_table_name).collect()[0]

print('Successfully found table {} in Cloud SQL Hive metastore'.format(
    test_table.TBL_NAME))

# Clean up table.
sqlContext.sql('DROP TABLE ' + test_table_name)
