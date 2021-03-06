from stackapi import StackAPI
import time
import datetime
import requests
import csv
import argparse
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

SITE = StackAPI('stackoverflow')
TIMESTR = time.strftime("%Y%m%d-%H%M%S")

KEYS = open('client_secrets.csv', 'rb')
KEYS_READ = csv.reader(KEYS)
next(KEYS_READ, None)

for row in KEYS_READ:
    CLIENT_ID = row[0]
    SITE.key = row[1]
    SITE.access_token = row[2]
KEYS.close()


def token(options):
    requests.get('https://stackexchange.com/oauth/dialog?client_id=' + CLIENT_ID + '&scope=no_expiry&'
                        'redirect_uri=https://stackexchange.com/oauth/login_success/')
    url = 'https://stackexchange.com/oauth/dialog?client_id=' + CLIENT_ID + \
          '&redirect_uri=https%3a%2f%2fstackexchange.com%2foauth%2flogin_success%2f&scope=no_expiry' \
          '&response_type=token&state=&returnurl=%2foauth%2fdialog%3fclient_id%3d' + CLIENT_ID + \
          '%26redirect_uri%3dhttps%253a%252f%252fstackexchange.com%252foauth' \
          '%252flogin_success%252f%26scope%3dno_expiry%26response_type%3dtoken%26state%3d'

    print url

def search(options):
    ########################################################
    from_date = options.from_date
    to_date = options.to_date
    SITE.page_size = options.max
    SITE.max_pages = 1
    min_answers = 1
    ########################################################

    results = "keyword_results_" + TIMESTR + ".csv"
    k = open(options.file, "rb")
    w = open(results, "w+")

    kr = csv.reader(k)
    wr = csv.writer(w)

    wr.writerow(['keyword', 'question_title', 'closed_date', 'tags', 'answer_id',
                 'answer_user_id', 'answer_user_name', 'answer_user_profile_url', 'answer_user_reputation',
                 'answer_score', 'age', 'location', 'website_url'])

    fromdate = int(time.mktime(datetime.datetime.strptime(from_date, '%m/%d/%Y').timetuple()))
    todate = int(time.mktime(datetime.datetime.strptime(to_date, '%m/%d/%Y').timetuple()))

    next(kr, None)
    for row in kr:

        keyword = row[0]
        tagged = row[1]
        title = row[2]
        body = row[3]

        response = SITE.fetch('search/advanced', fromdate=fromdate, todate=todate, accepted=True, closed=True,
                              answers=min_answers, sort='votes', q=keyword, title=title, body=body, tagged=tagged)

        for questions in response['items']:
            question_title = questions['title']
            closed_date = datetime.datetime.fromtimestamp(questions['closed_date']).strftime('%m/%d/%Y')
            answer_id = str(questions['accepted_answer_id'])
            tags = questions['tags']

            answers = SITE.fetch('answers/' + answer_id)

            for answer in answers['items']:
                answer_user_id = answer['owner']['user_id']
                answer_user_name = answer['owner']['display_name']
                answer_user_profile_url = answer['owner']['link']
                answer_user_reputation = answer['owner']['reputation']
                answer_score = answer['score']

                user_data = SITE.fetch('users/' + str(answer_user_id) + '/')

                for data in user_data['items']:
                    try:
                        age = data['age']
                    except KeyError:
                        age = 'n/a'
                    try:
                        location = data['location']
                    except KeyError:
                        location = 'n/a'

                    try:
                        website_url = data['website_url']
                    except KeyError:
                        website_url = 'n/a'

                wr.writerow([keyword, question_title, closed_date, tags, answer_id, answer_user_id, answer_user_name,
                             answer_user_profile_url, answer_user_reputation, answer_score, age, location, website_url])

    print 'File Ready: ' + results

    k.close()
    w.close()


def topics(options):
    ########################################################
    SITE.page_size = options.max
    SITE.max_pages = 1
    all_time = options.all_time
    ########################################################

    results = "topic_results_" + TIMESTR + ".csv"
    t = open(options.file, "rb")
    u = open(results, "w+")

    tr = csv.reader(t)
    ur = csv.writer(u)

    ur.writerow(['topic', 'user_id', 'display_name', 'profile_url', 'reputation', 'accept_rate', 'post_count',
                 'score', 'age', 'location', 'website_url'])

    if all_time:
        time_frame = 'all_time'
    else:
        time_frame = 'month'

    for row in tr:

        topic = ''.join(row)
        response = SITE.fetch('tags/{tag}/top-answerers/' + time_frame, tag=topic)

        for user in response['items']:
            user_id = user['user']['user_id']
            display_name = user['user']['display_name']
            profile_url = user['user']['link']
            post_count = user['post_count']
            score = user['score']
            try:
                accept_rate = user['user']['accept_rate']
            except KeyError:
                accept_rate = 'n/a'
            try:
                reputation = user['user']['reputation']
            except KeyError:
                reputation = 'n/a'

            user_data = SITE.fetch('users/' + str(user_id) + '/')

            for data in user_data['items']:
                try:
                    age = data['age']
                except KeyError:
                    age = 'n/a'
                try:
                    location = data['location']
                except KeyError:
                    location = 'n/a'

                try:
                    website_url = data['website_url']
                except KeyError:
                    website_url = 'n/a'

            ur.writerow([topic, user_id, display_name, profile_url, reputation, accept_rate, post_count,
                             score, age, location, website_url])

    print 'File Ready: ' + results

    t.close()
    u.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    FUNCTION_MAP = {'topics': topics,
                    'search': search,
                    'token': token}

    parser.add_argument('command', choices=FUNCTION_MAP.keys())
    parser.add_argument("--file", help="Input CSV name", default="topics.csv")
    parser.add_argument("--from_date", help="Keyword Search Only: From Date", default="01/01/2017")
    parser.add_argument("--to_date", help="Keyword Search Only: To Date", default=time.strftime("%m/%d/%Y"))
    parser.add_argument("--all_time", help="Topic Search Only: All Time", default=False)
    parser.add_argument("--max", help="Max Results", default=10)

    args = parser.parse_args()

    func = FUNCTION_MAP[args.command]
    func(args)
