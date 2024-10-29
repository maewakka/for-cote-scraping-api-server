import requests
from bs4 import BeautifulSoup
from models.db_connection import get_db_connection
import json


class ProblemService:
    def __init__(self):
        self.base_url = 'https://www.acmicpc.net'

    def scrape_step_problems(self, step_id):
        """특정 단계의 문제 목록을 웹에서 가져와 반환하는 메서드"""
        url = f'{self.base_url}/step/{step_id}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch problems for step {step_id}, status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        problems = []
        problem_rows = soup.select('#problemset tbody tr')
        for i in range(0, len(problem_rows), 2):
            correct_percentage = problem_rows[i].select_one('td:nth-of-type(7)').text.strip().replace('%', '')
            correct_percentage = float(correct_percentage) if correct_percentage else 0.0

            problems.append({
                'step': step_id,
                'problem_id': problem_rows[i].select_one('td:nth-of-type(2)').text.strip(),
                'title': problem_rows[i].select_one('td:nth-of-type(3) a').text.strip(),
                'solved_count': problem_rows[i].select_one('td:nth-of-type(5) a').text.strip(),
                'submission_count': problem_rows[i].select_one('td:nth-of-type(6) a').text.strip(),
                'correct_percentage': correct_percentage,
                'description': problem_rows[i + 1].text.strip() if i + 1 < len(problem_rows) else ""
            })

        return problems

    def save_step_problems_to_db(self, step_id, problems):
        """단계별 문제 목록을 DB에 저장하는 메서드"""
        conn = get_db_connection()
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
            problem['problem_id'], step_id, problem['title'], problem['description'], problem['solved_count'],
            problem['submission_count'], problem['correct_percentage']))
        conn.commit()
        cursor.close()
        conn.close()

    def scrape_problem_details(self, problem_id):
        """웹에서 특정 문제의 상세 정보를 가져오는 메서드"""
        url = f'{self.base_url}/problem/{problem_id}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        problem_title = soup.find('span', id='problem_title').text.strip()
        problem_description = str(soup.find('div', id='problem_description'))
        problem_input = soup.find('div', id='problem_input').text.strip()
        problem_output = soup.find('div', id='problem_output').text.strip()

        sample_inputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-input'))
        sample_outputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-output'))
        examples = [{'input': inp.text, 'output': out.text} for inp, out in zip(sample_inputs, sample_outputs)]

        return {
            'title': problem_title,
            'description': problem_description,
            'input': problem_input,
            'output': problem_output,
            'examples': examples
        }

    def save_problem_details_to_db(self, problem_id, problem_data):
        """특정 문제의 상세 정보를 DB에 저장하는 메서드"""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO problems (problem_id, title, description, input, output, examples, update_count)
            VALUES (%s, %s, %s, %s, %s, %s, 10000)
            ON DUPLICATE KEY UPDATE 
                title = VALUES(title), description = VALUES(description),
                input = VALUES(input), output = VALUES(output), examples = VALUES(examples), update_count = 10000
        """
        cursor.execute(query, (
        problem_id, problem_data['title'], problem_data['description'], problem_data['input'], problem_data['output'],
        json.dumps(problem_data['examples'], ensure_ascii=False)))
        conn.commit()
        cursor.close()
        conn.close()

    def get_step_problems(self, step_id):
        """DB에서 단계별 문제 목록을 조회하고 없으면 스크래핑 후 저장"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM step_problems WHERE step_id = %s"
        cursor.execute(query, (step_id,))
        problems = cursor.fetchall()

        if not problems:
            problems = self.scrape_step_problems(step_id)
            self.save_step_problems_to_db(step_id, problems)

        cursor.close()
        conn.close()
        return problems
