from models.baekjoon_scraper import BaekjoonScraper
from models.db_connection import get_db_connection

class StepService:
    def __init__(self):
        self.scraper = BaekjoonScraper()

    def get_all_steps(self):
        """모든 단계 정보를 DB에서 조회하고 없으면 스크래핑 후 저장"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # DB에서 단계 정보 조회
        query = "SELECT * FROM steps"
        cursor.execute(query)
        steps = cursor.fetchall()

        # 만약 DB에 데이터가 없다면 스크래핑 후 저장
        if not steps:
            steps = self.scraper.get_steps()  # 스크래핑으로 단계 정보 가져오기
            self.save_steps_to_db(steps)  # DB에 저장

        cursor.close()
        conn.close()
        return steps

    def get_step_problems(self, step_id):
        """특정 단계의 문제 정보를 DB에서 조회하고 없으면 스크래핑 후 저장"""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # DB에서 특정 단계의 문제 정보 조회
        query = "SELECT * FROM step_problems WHERE step_id = %s"
        cursor.execute(query, (step_id,))
        problems = cursor.fetchall()

        # 만약 DB에 데이터가 없다면 스크래핑 후 저장
        if not problems:
            problems = self.scraper.get_step_problems(step_id)  # 스크래핑으로 문제 정보 가져오기
            self.save_step_problems_to_db(step_id, problems)  # DB에 저장

        cursor.close()
        conn.close()
        return problems

    def save_steps_to_db(self, steps):
        """단계 정보를 DB에 저장하는 메서드"""
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
        """문제 정보를 DB에 저장하는 메서드"""
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
