import re
import codecs
import urllib2
from bs4 import BeautifulSoup

def test_url(date, part=1):
	return 'http://www4.student.liu.se/tentaresult/?search=1&datum='+date+'&part='+str(part)

def parse_all_date_tests(date):
	all_tests = []
	part = 1
	while True:
		html = urllib2.urlopen(test_url( date, part )).read()
		part += 10
		tests = parse_tests(html)
		if tests == []:
			break
		else:
			all_tests.extend(tests)
	return all_tests

def parse_course_info(course):
	course = course.split(':')
	course_id = course[0]
	course_descr_raw = ':'.join(course[1:])
	try:
		course_hp = re.search('[0-9]*\.[0-9]* hp', course_descr_raw).group(0)
		course_description = course_descr_raw.replace(course_hp, '').strip()
		course_hp = float(course_hp.split(' ')[0])
	except:
		course_description = course_descr_raw
		course_hp = -1.0

	course_description = course_description.replace(',','.')
	course_description = course_description.replace('"',"'")

	return { 'id': course_id, 'desc': course_description, 'hp': course_hp }

def parse_grades(grades):
	rotated_grades = grades[-1:]+grades[:-1]
	zipped_grades = zip(grades, rotated_grades)
	return [ grade[1] for grade in enumerate(zipped_grades) if grade[0]%2==0 ]

def parse_tests(html):
	soup = BeautifulSoup(html)
	tests = []
	for color in ['#FFFFFF', '#FFFFCC']:
		for test in soup('tr', {'bgcolor': color}):
			strings = list(test.stripped_strings)
			course_info = parse_course_info(strings[0])
			test_info = parse_course_info(strings[1])
			date = strings[2]
			grades = parse_grades(strings[5:])
			tests.append({
				'date': date,
				'course': course_info,
				'test': test_info,
				'grades': grades
			})

	return tests

def format_grades(tests):
	string = ''
	for test in tests:
		for grade in test['grades']:
			string += '"' + '","'.join([
				test['date'],
				test['course']['id'],
				test['test']['id'],
				grade[0],
				grade[1]
			])
			string += '"\n'
	return string

def save_test_results(years, months, days, print_progress=True):
	f = codecs.open('grades2.csv', 'w', 'utf-8')
	f.write('"date","course_id","test_id","grade","count"\n')

	courses = {}
	tests = {}
	for year in years:
		for month in months:
			for day in days:
				date = '-'.join(map(str, [year, month, day]))
				if print_progress:
					print date

				parsed_tests = parse_all_date_tests(date)

				for test in parsed_tests:
					courses.update({ test['course']['id']:
						[ test['course']['hp'], test['course']['desc'] ] })
					tests.update({ test['test']['id']:
						[ test['course']['id'], test['test']['hp'], test['test']['desc'] ] })

				formatted_grades = format_grades(parsed_tests)
				if formatted_grades != '':
					f.write(formatted_grades)

	f.close()

	if print_progress:
		print 'Finished requests!'

	# Helper func to help the code stay DRY
	def save_dict(dct, field_names, file_name, format_method):
		f = codecs.open(file_name, 'w', 'utf-8')
		f.write(field_names+'\n')

		for id in dct.keys():
			row = ''
			for field in format_method(id):
				if type(field) in [float, int]:
					row += str(field) + ','
				else:
					row += '"' + field + '",'
			# Remove the last comma
			f.write(row[:-1] + '\n')

		f.close()

	save_dict(courses, '"course_id","hp","descr"', 'courses2.csv',
			lambda id: [id] + courses[id])
	save_dict(tests, '"test_id","course_id","hp","descr"', 'tests2.csv',
			lambda id: [id] + tests[id])

	if print_progress:
		print 'Done!'

#save_test_results(range(2000,2014), range(1,13), range(1, 32))
