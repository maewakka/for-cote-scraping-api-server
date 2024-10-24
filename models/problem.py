import re
import requests
from bs4 import BeautifulSoup
import json
from models.db_connection import get_db_connection


class Problem:
    def __init__(self, problem_id):
        self.problem_id = problem_id

    def fetch_from_web(self):
        """웹에서 문제 정보를 가져오는 메서드"""
        url = f'https://www.acmicpc.net/problem/{self.problem_id}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 문제 제목 가져오기 (없을 경우 None 처리)
        title_tag = soup.find('span', id='problem_title')
        if title_tag is None:
            raise Exception(f"Problem title not found for problem_id {self.problem_id}")
        problem_title = title_tag.text.strip()

        # 문제 설명, 입력, 출력 가져오기 (없을 경우 처리)
        problem_description = soup.find('div', id='problem_description') or soup.find('section', id='custom_dislocation')
        if problem_description is None:
            raise Exception(f"Problem description not found for problem_id {self.problem_id}")
        problem_description = str(problem_description)

        problem_input = soup.find('div', id='problem_input')
        if problem_input is None:
            raise Exception(f"Problem input not found for problem_id {self.problem_id}")
        problem_input = problem_input.text.strip()

        problem_output = soup.find('div', id='problem_output')
        if problem_output is None:
            raise Exception(f"Problem output not found for problem_id {self.problem_id}")
        problem_output = problem_output.text.strip()

        # 예제 입력/출력 처리
        sample_inputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-input'))
        sample_outputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-output'))

        examples = []
        for sample_input, sample_output in zip(sample_inputs, sample_outputs):
            examples.append({
                'input': sample_input.text.strip(),
                'output': sample_output.text.strip()
            })

        return {
            'title': problem_title,
            'description': problem_description,
            'input': problem_input,
            'output': problem_output,
            'examples': examples
        }

    def fetch_from_db(self):
        """DB에서 문제 정보를 가져오는 메서드"""
        conn = get_db_connection()
        if conn is None:
            return None

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM problems WHERE problem_id = %s"
        cursor.execute(query, (self.problem_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return {
                'title': result['title'],
                'description': result['description'],
                'input': result['input'],
                'output': result['output'],
                'examples': json.loads(result['examples']),
                'update_count': result['update_count']
            }
        return None

    def save_or_update_problem_in_db(self, problem_data):
        """문제를 DB에 저장하거나 업데이트하는 메서드"""
        try:
            conn = get_db_connection()
            if conn is None:
                return

            cursor = conn.cursor()

            # UPSERT 쿼리: 문제를 삽입하거나 업데이트하는 쿼리
            query = """
                INSERT INTO problems (problem_id, title, description, input, output, examples, update_count)
                VALUES (%s, %s, %s, %s, %s, %s, 10000)
                ON DUPLICATE KEY UPDATE 
                    title = VALUES(title),
                    description = VALUES(description),
                    input = VALUES(input),
                    output = VALUES(output),
                    examples = VALUES(examples),
                    update_count = 10000
            """
            cursor.execute(query, (
                self.problem_id,
                problem_data['title'],
                problem_data['description'],
                problem_data['input'],
                problem_data['output'],
                json.dumps(problem_data['examples'], ensure_ascii=False)
            ))
            conn.commit()
        except Exception as e:
            print(f"Error saving or updating problem in DB: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def decrement_update_count(self):
        """DB에서 update_count를 1 감소시키는 메서드"""
        conn = get_db_connection()

        if conn is None:
            return

        cursor = conn.cursor()
        query = "UPDATE problems SET update_count = update_count - 1 WHERE problem_id = %s"
        cursor.execute(query, (self.problem_id,))
        conn.commit()
        cursor.close()
        conn.close()

    def get_problem_details(self):
        """문제 정보를 DB에서 가져오거나, 없으면 웹에서 가져온 후 저장하는 메서드"""
        problem_data = self.fetch_from_db()
        if not problem_data:
            # 문제 정보가 DB에 없으면 웹에서 가져와서 저장
            problem_data = self.fetch_from_web()
            self.save_or_update_problem_in_db(problem_data)
        elif problem_data['update_count'] <= 0:
            # update_count가 0이면 웹에서 다시 가져와서 업데이트
            problem_data = self.fetch_from_web()
            self.save_or_update_problem_in_db(problem_data)

        # update_count를 1 감소
        self.decrement_update_count()
        return problem_data
