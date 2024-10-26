import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


def load_env_file():
    """환경 파일을 우선 지정된 경로에서 불러오고 실패 시 기본 경로에서 불러오는 함수"""
    try:
        if not load_dotenv('/config/.env'):
            raise FileNotFoundError()
    except FileNotFoundError as e:
        # 기본 경로에서 다시 시도
        load_dotenv()


def get_db_connection():
    """MySQL 데이터베이스에 연결하는 함수 (환경 변수를 통해 연결)"""
    load_env_file()  # 환경 변수를 로드하는 함수 호출

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
