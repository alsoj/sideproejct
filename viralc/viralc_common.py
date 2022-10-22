import pymysql
import viralc_config

def get_db_connection():
    """
    MySQL DB connect
    :return: DB connection
    """
    return pymysql.connect(
        host=viralc_config.DATABASE_CONFIG['host'],
        user=viralc_config.DATABASE_CONFIG['user'],
        password=viralc_config.DATABASE_CONFIG['password'],
        db=viralc_config.DATABASE_CONFIG['dbname'],
        charset='utf8')