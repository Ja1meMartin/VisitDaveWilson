from __future__ import print_function
from .models import create_statement, Flight
from flask import Flask, request, session, redirect, url_for, render_template, flash
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


app = Flask(__name__)

def p(*args):
	for text in args:
		print (text, file=sys.stderr)
		
def date_to_list(date):

	if date == '': 
		return [None,None]
	try:
		d = int(date)
		return [d, None]
	except:
		pass
	if '-' in date: return [int(date.split('-')[0]), '<=']
	if '+' in date: return [int(date.split('+')[0]), '>=']
    
	return [int(x) for x in date.split()]



@app.route('/register', methods=['GET','POST'])
def register():

	s = "In Register function Views.py"	
	flash(s)
	p(s)
		
	if request.method == 'POST':
	
		p("In The Damn Thing")
		location, name, date, day =  (request.form[x] for x in ('startLocation', 'startName', 'startDate', 'startDay') )
		
		"""
			location: Airport, City, Region, Country or Continent. When option box will I remove title?
			name: CSV of locations i.e for city Dublin, London, Paris although most frequently will be one 
			
		"""
		p ("got start values")
		p ("---".join([location, name, date, day]))
		name = [n.strip() for n in name.split(',')]
		location = location.title()
		date = date_to_list(date)
		
		if day == '':
			day = None
		else:
			try:
				day = int(day)
				day = day % 7
			except:
				weekdays = ['su','mo','tu','we','th','fr','sa']
				day = weekdays.index(day.lower()[:2])
				
		start = (location, name, date, day)
		
		stops = []
		
		p ("FINISHED start values")
		[p (x) for x in [location, name, date, day]]
		
		for x in ('stop1Location', 'stop1Name', 'stop1Duration', 'stop1Leave'):
			p(x)
			p(request.form[x])
		
		
		
		location, name, duration, leave = (request.form[x] for x in ('stop1Location', 'stop1Name', 'stop1Duration', 'stop1Leave') )
		
		p ("got STOP1 values")
		p ("---".join([location, name, duration, leave]))
		
		if name is not '':
			location = location.title()
			duration = int(duration)
			leave = None if leave == '' else leave
			
			stop = (location, name, duration, leave)
			p("ADD STOP", stop)
			
			stops.append(stop)
			
			p("STOPS", stops)
			
		p ("FINISHED STOP1 values")
		[p (x) for x in [location, name, duration, leave]]
			
		location, name, duration, leave = (request.form[x] for x in ('stop2Location', 'stop2Name', 'stop2Duration', 'stop2Leave') )
		
		p ("got STOP2 values")
		p ("---".join([location, name, duration, leave]))
		
		if name is not '':
			location = location.title()
			duration = int(duration)
			leave = None if leave == '' else leave
			
			stop = (location, name, duration, leave)
			p("ADD STOP", stop)
			
			stops.append(stop)
			
			p("STOPS", stops)
			
		p ("FINISHED STOP2 values")
		[p (x) for x in [location, name, duration, leave]]
		
		location, name, duration, leave = (request.form[x] for x in ('destLocation', 'destName', 'destDuration', 'destLeave') )
		
		p ("got DESTINATION values")
		p ("---".join([location, name, duration, leave]))
		
		destination = None
		
		if name is not '':
			location = location.title()
			duration = int(duration)
			leave = None if leave == '' else leave
			
			destination = (location, name, duration, leave)
			p("ADD DESTINATION", destination)
			
			
		p ("FINISHED DEST values")
		[p (x) for x in [location, name, duration, leave]]
		
		p("START", start)
		p("STOPs", stops)
		p("DESTINATION", destination)
		
		for record in create_statement(start, stops, destination):
			"""
				
			"""
			flash ( record ['f1'] )
			flash ( Flight(record ['f1']).html_list_element())
			flash ( record )
			flash ( type ( record ['f1'] ) )
			try:
				flash ( record['f1']['destination'] )
			except:
				flash("Index cost did not work")
			
		flash(s)

	p("RENDER TEMPLATE")	

	return render_template('register.html')