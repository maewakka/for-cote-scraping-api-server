import requests
from bs4 import BeautifulSoup
from models.db_connection import get_db_connection

class BaekjoonScraper:
    def __init__(self):
        self.base_url = 'https://www.acmicpc.net'

    def scrape_steps(self):
        """웹에서 단계 목록을 가져와 반환하는 메서드"""
        url = f'{self.base_url}/step'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
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

                step_data = {
                    'step': step_id,
                    'title': step_link.text.strip(),
                    'description': step_row.select_one('td:nth-of-type(3)').text.strip(),
                    'problems_count': step_row.select_one('td:nth-of-type(5)').text.strip(),
                }
                steps.append(step_data)

        return steps

    def scrape_step_problems(self, step_id):
        """웹에서 특정 단계의 문제 목록을 가져와 반환하는 메서드"""
        url = f'{self.base_url}/step/{step_id}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch problems for step {step_id}, status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        problems = []

        # 문제 목록을 파싱하는 로직
        problem_rows = soup.select('#problemset tbody tr')  # 문제 테이블의 행 선택

        for i in range(0, len(problem_rows), 2):  # 문제 정보와 설명이 번갈아 나옴
            correct_percentage_text = problem_rows[i].select_one('td:nth-of-type(7)').text.strip()
            try:
                correct_percentage = float(correct_percentage_text.replace('%', '')) if correct_percentage_text else 0.0
            except ValueError:
                correct_percentage = 0.0  # 비정상적인 값이 들어올 경우 0.0으로 처리

            problem_data = {
                'step': step_id,
                'problem_id': problem_rows[i].select_one('td:nth-of-type(2)').text.strip(),
                'title': problem_rows[i].select_one('td:nth-of-type(3) a').text.strip(),
                'solved_count': problem_rows[i].select_one('td:nth-of-type(5) a').text.strip(),
                'submission_count': problem_rows[i].select_one('td:nth-of-type(6) a').text.strip(),
                'correct_percentage': correct_percentage,  # 정답 비율 처리
                'description': problem_rows[i + 1].text.strip() if i + 1 < len(problem_rows) else ""  # 설명 (다음 행에 존재)
            }
            problems.append(problem_data)

        return problems

    def save_steps_to_db(self, steps):
        """단계 목록을 DB에 저장하는 메서드"""
        conn = get_db_connection()
        if conn is None:
            return

        cursor = conn.cursor()

        for step in steps:
            query = """
                INSERT INTO steps (step_id, title, description, problems_count)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    title = VALUES(title), description = VALUES(description),
                    problems_count = VALUES(problems_count), last_update = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (
                step['step'],
                step['title'],
                step['description'],
                step['problems_count']
            ))

        conn.commit()
        cursor.close()
        conn.close()

    def save_step_problems_to_db(self, step_id, problems):
        """문제 목록을 DB에 저장하는 메서드"""
        conn = get_db_connection()
        if conn is None:
            return

        cursor = conn.cursor()

        for problem in problems:
            query = """
                INSERT INTO step_problems (problem_id, step_id, title, description, solved_count, submission_count, correct_percentage)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    title = VALUES(title), description = VALUES(description),
                    solved_count = VALUES(solved_count), submission_count = VALUES(submission_count),
                    correct_percentage = VALUES(correct_percentage)
            """
            cursor.execute(query, (
                problem['problem_id'],
                step_id,
                problem['title'],
                problem['description'],
                problem['solved_count'],
                problem['submission_count'],
                problem['correct_percentage']
            ))

        conn.commit()
        cursor.close()
        conn.close()

    def scrape_and_update_steps(self):
        """단계 목록을 스크래핑하고 DB에 저장하는 메서드"""
        steps = self.scrape_steps()
        print(steps)
        self.save_steps_to_db(steps)

    def scrape_and_update_problems(self):
        """모든 단계의 문제를 스크래핑하고 DB에 저장하는 메서드"""
        steps = self.scrape_steps()
        for step in steps:
            step_id = step['step']
            problems = self.scrape_step_problems(step_id)
            print(problems)
            self.save_step_problems_to_db(step_id, problems)
