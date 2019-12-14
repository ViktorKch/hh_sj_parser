import requests
from itertools import count
import os
from dotenv import load_dotenv
from terminaltables import SingleTable

LANGUAGES = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go', 'Shell' ]

def predict_salary(salary_from, salary_to):
    if not salary_from and salary_to:
        return salary_to * 0.8
    elif salary_from and not salary_to:
        return salary_from * 1.2
    return (salary_from + salary_to) / 2

def predict_salary_hh(salary):
    if salary['currency'] != 'RUR':
        return None
    return predict_salary(salary['from'], salary['to'])

def predict_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])

def print_table(stats_by_site, title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language, info in stats_by_site.items():
        table_data += [language, info['vacancies_found'], info['vacancies_processed'], info['average_salary']],
    table_instance = SingleTable(table_data, title)
    print(table_instance.table)

def get_hh_statistics(languages, city_code=1, vacancy_period=30):
    hh_statistics = {}
    hh_url = 'https://api.hh.ru/vacancies'
    for language in languages:
        all_vacancy_salaries = []
        sum_of_salaries = 0
        salaries_counter = 0
        hh_params = {
            'text': f'Программист {language}',
            'area': city_code,
            'period': vacancy_period,
            'only_with_salary': True,
        }
        for page in count(0):
            hh_params.update({'page': page})
            page_response = requests.get(hh_url, hh_params)
            page_response.raise_for_status()
            page_data = page_response.json()
            all_vacancies_found = page_data['found']
            vacancies_per_page = page_data['items']

            for vacancy in vacancies_per_page:
                all_vacancy_salaries.append(vacancy['salary'])

            if page >= 99:
                break

        for salary in all_vacancy_salaries:
            if predict_salary_hh(salary) != None:
                sum_of_salaries += predict_salary_hh(salary)
                salaries_counter += 1

        try:
            average_salary = int(sum_of_salaries / salaries_counter)
        except ZeroDivisionError:
            average_salary = 0

        language_statistic = {
            'vacancies_found': all_vacancies_found,
            'vacancies_processed': salaries_counter,
            'average_salary': average_salary
        }

        hh_statistics[language] = language_statistic
    return hh_statistics

def get_sj_statistics(languages, town='Москва'):
    sj_statistics = {}
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    for language in languages:
        all_vacancy_salaries = []
        sum_of_salaries = 0
        salaries_counter = 0
        sj_headers = {
            'X-Api-App-Id': os.getenv('SECRET_KEY')
        }
        sj_params = {
            'keyword': f'Программист {language}',
            'town': town,
        }
        for page in count(0):
            sj_params.update({'page': page})
            page_response = requests.get(sj_url, headers=sj_headers, params=sj_params)
            page_response.raise_for_status()
            page_data = page_response.json()
            all_vacancies_found = page_data['total']
            vacancies_per_page = page_data['objects']

            for vacancy in vacancies_per_page:
                all_vacancy_salaries.append(predict_salary_sj(vacancy))

            if not page_data['more']:
                break

        for salary in all_vacancy_salaries:
            if salary != 0 and salary != None:
                sum_of_salaries += salary
                salaries_counter += 1

        try:
            average_salary = int(sum_of_salaries / salaries_counter)
        except ZeroDivisionError:
            average_salary = 0

        language_statistic = {
            'vacancies_found': all_vacancies_found,
            'vacancies_processed': salaries_counter,
            'average_salary': average_salary
        }
        sj_statistics[language] = language_statistic
    return sj_statistics

if __name__ == '__main__':
    load_dotenv()
    print_table(get_hh_statistics(LANGUAGES), 'HeadHunter Moscow')
    print_table(get_sj_statistics(LANGUAGES), 'SuperJob Moscow')

