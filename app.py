from flask import Flask, jsonify
from flask_apscheduler import APScheduler
from services.step_service import StepService
from services.problem_service import ProblemService

class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

step_service = StepService()
problem_service = ProblemService()

@app.route('/step', methods=['GET'])
def get_all_steps():
    steps = step_service.get_all_steps()
    return jsonify(steps)

@app.route('/step/<int:step_id>', methods=['GET'])
def get_step_problems(step_id):
    problems = problem_service.get_step_problems(step_id)
    return jsonify(problems)

@app.route('/problem/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem_data = problem_service.scrape_problem_details(problem_id)
    problem_service.save_problem_details_to_db(problem_id, problem_data)
    return jsonify(problem_data)

@scheduler.task('cron', id='scrape_steps', hour='23', minute=5)
def scheduled_scrape_steps():
    steps = step_service.scrape_steps()
    for step in steps:
        step_id = step['step']
        problems = problem_service.scrape_step_problems(step_id)
        print(problems)
        problem_service.save_step_problems_to_db(step_id, problems)

    print("update_completed!")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=7000)