import requests
from bs4 import BeautifulSoup
from models.db_connection import get_db_connection


class StepService:
    def __init__(self):
        self.base_url = 'https://www.acmicpc.net'

    def scrape_steps(self):
        """단계 목록을 웹에서 가져와 반환하는 메서드"""
        url = f'{self.base_url}/step'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch steps, status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        steps = []
        for step_row in soup.select('.table tbody tr'):
            step_link = step_row.select_one('td:nth-of-type(2) a')
            if step_link:
                href = step_link['href']
                step_id = href.split('/')[-1]
                steps.append({
                    'step': step_id,
                    'title': step_link.text.strip(),
                    'description': step_row.select_one('td:nth-of-type(3)').text.strip(),
                    'problems_count': step_row.select_one('td:nth-of-type(5)').text.strip(),
                })

        return steps

    def save_steps_to_db(self, steps):
        """단계 목록을 DB에 저장하는 메서드"""
        conn = get_db_connection()
        cursor = conn.cursor()
        for step in steps:
            query = """
                INSERT INTO steps (step_id, title, description, problems_count)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    title = VALUES(title), description = VALUES(description),
                    problems_count = VALUES(problems_count), last_update = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (step['step'], step['title'], step['description'], step['problems_count']))
        conn.commit()
        cursor.close()
        conn.close()

    def get_all_steps(self):
        """DB에서 단계 목록을 조회하고 없으면 스크래핑 후 저장"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM steps"
        cursor.execute(query)
        steps = cursor.fetchall()

        if not steps:  # DB에 데이터가 없을 경우 스크래핑 후 저장
            steps = self.scrape_steps()
            self.save_steps_to_db(steps)

        cursor.close()
        conn.close()
        return steps
