from decimal import Decimal

from flask import Flask, jsonify, make_response, Response
from flask_apscheduler import APScheduler
from models.baekjoon_scraper import BaekjoonScraper
from models.step_service import StepService
from models.problem import Problem
import json

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

scraper = BaekjoonScraper()
step_service = StepService()

from functools import wraps

def as_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        res = f(*args, **kwargs)
        res = json.dumps(res, ensure_ascii=False).encode('utf8')
        return Response(res, content_type='application/json; charset=utf-8')
    return decorated_function

def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

# 모든 단계 정보를 반환하는 엔드포인트
@app.route('/step', methods=['GET'])
def get_all_steps():
    """모든 단계 정보를 반환하는 API"""
    try:
        data = step_service.get_all_steps()  # StepService를 통해 단계 정보 가져오기
        response = make_response(jsonify(data))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# 특정 단계의 문제 정보를 반환하는 엔드포인트
@app.route('/step/<int:step_id>', methods=['GET'])
def get_step_problems(step_id):
    """특정 단계의 문제 정보를 반환하는 API"""
    try:
        data = step_service.get_step_problems(step_id)  # StepService에서 문제 정보 가져오기

        response = make_response(jsonify(data))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# 특정 문제 정보를 반환하는 엔드포인트
@app.route('/problem/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """특정 문제의 정보를 반환하는 API"""
    try:
        problem = Problem(problem_id)  # Problem 클래스의 인스턴스 생성
        data = problem.get_problem_details()  # 문제 데이터 가져오기
        response = make_response(jsonify(data))
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

# 스케줄러로 특정 시각마다 단계와 문제 목록을 업데이트
@scheduler.task('cron', id='scrape_and_update_steps', hour=16, minute=1)
def scheduled_scrape_steps():
    scraper.scrape_and_update_steps()
    print("Steps scraped and updated.")

@scheduler.task('cron', id='scrape_and_update_problems', hour=16, minute=4)
def scheduled_scrape_problems():
    scraper.scrape_and_update_problems()
    print("Problems scraped and updated.")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=7000)
