from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import sessionmaker
from models import Problem

class ProblemScraper:

    def __init__(self, db_engine):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.db_session = sessionmaker(bind=db_engine)()

    # 데이터베이스에서 문제 조회
    def get_problem_from_db(self, problem_id):
        return self.db_session.query(Problem).filter_by(problem_id=problem_id).first()

    # 웹에서 문제 정보 스크래핑
    def scrape_problem(self, problem_id):
        print(f"Fetching problem {problem_id}")
        url = f'https://www.acmicpc.net/problem/{problem_id}'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 문제 제목
        problem_title = soup.find('span', id='problem_title').text.strip()

        # 문제 설명 (HTML 형식)
        problem_description = str(soup.find('div', id='problem_description'))

        # 입력 설명
        problem_input = soup.find('div', id='problem_input').text.strip()

        # 출력 설명
        problem_output = soup.find('div', id='problem_output').text.strip()

        # 예제 입력/출력
        sample_inputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-input'))
        sample_outputs = soup.find_all('pre', id=lambda x: x and x.startswith('sample-output'))

        examples = []
        for i, (sample_input, sample_output) in enumerate(zip(sample_inputs, sample_outputs)):
            examples.append({
                'input': sample_input.text.strip(),
                'output': sample_output.text.strip()
            })

        return {
            'problem_id': problem_id,
            'title': problem_title,
            'description': problem_description,
            'input': problem_input,
            'output': problem_output,
            'examples': examples
        }

    # 스크래핑한 문제를 데이터베이스에 저장
    def save_problem_to_db(self, problem_data):
        new_problem = Problem(
            problem_id=problem_data['problem_id'],
            title=problem_data['title'],
            description=problem_data['description'],
            input_description=problem_data['input'],
            output_description=problem_data['output'],
            examples=problem_data['examples']  # JSON을 텍스트로 저장
        )
        self.db_session.add(new_problem)
        self.db_session.commit()

    # 문제 조회 로직 (DB -> 스크래핑 -> DB 저장)
    def get_problem_details(self, problem_id):
        # 먼저 데이터베이스에서 문제를 찾음
        problem = self.get_problem_from_db(problem_id)
        if problem:
            # DB에서 문제가 있을 경우 반환
            return {
                'problem_id': problem.problem_id,
                'title': problem.title,
                'description': problem.description,
                'input': problem.input_description,
                'output': problem.output_description,
                'examples': problem.examples
            }
        else:
            # DB에 문제가 없을 경우 스크래핑하여 DB에 저장
            scraped_data = self.scrape_problem(problem_id)
            self.save_problem_to_db(scraped_data)
            return scraped_data
