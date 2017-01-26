from __future__ import print_function
from .models import create_statement, Flight, Trip, Start
#import .formparts 
from flask import Flask, request, session, redirect, url_for, render_template, flash
import sys
import importlib
importlib.reload(sys)
# TODO
#sys.setdefaultencoding('utf-8')


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



	
@app.route('/wizard', methods = ['GET','POST'])
def wizard():
    p("IN Wizard - NEED TO FILL IN FROM SESSION VARIABLES")
    if request.method == 'POST':
        return request.form.get('start_airport')
    return render_template('wizard.html')


	
@app.route('/register', methods=['GET','POST'])
def register():
	trips = None

		
	if request.method == 'POST':
	
		return_flight = request.form.get('returnTrip')
	
		location, name, date, day =  (request.form[x] for x in ('startLocation', 'startName', 'startDate', 'startDay') )
		
		startNode = Start(location, name, date, day)
		
		"""
			location: Airport, City, Region, Country or Continent. When option box will I remove title?
			name: CSV of locations i.e for city Dublin, London, Paris although most frequently will be one 
			
		"""
		
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
		
		location, name, duration, leave = (request.form[x] for x in ('stop1Location', 'stop1Name', 'stop1Duration', 'stop1Leave') )
		
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
			if return_flight:
				return_flight = True
			
			destination = (location, name, duration, leave, return_flight)
			p("ADD DESTINATION", destination)
			
			
		p ("FINISHED DEST values")
		[p (x) for x in [location, name, duration, leave]]
		
		p("START", start)
		p("STOPs", stops)
		p("DESTINATION", destination)
		
		results = create_statement(start, stops, destination)
		
		trips = [Trip(result) for result in results]
		
		flash("HTML")
		
		for trip in trips:
			flash ( trip.html_list() )
		
		
		for record in results:
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
			
		

	p("RENDER TEMPLATE")	

	return render_template('register.html', trips=trips)