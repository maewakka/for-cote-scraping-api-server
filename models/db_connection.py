import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드 (필요한 경우)
# load_dotenv('/config/.env')
load_dotenv()
def get_db_connection():
    """MySQL 데이터베이스에 연결하는 함수 (환경 변수를 통해 연결)"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            port=os.getenv('MYSQL_PORT'),
            database=os.getenv('MYSQL_DATABASE'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            charset=os.getenv('MYSQL_CHARSET')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None
