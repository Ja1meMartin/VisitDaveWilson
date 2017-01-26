from __future__ import print_function
from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
from flask import flash
import os
import uuid
import datetime
import sys
import importlib
importlib.reload(sys)


# TODO
#sys.setdefaultencoding('utf-8')

url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')




graph = Graph(url + '/db/data/', username=username, password=password)

# Convenience method to print to standard error
def p(*args):
	for text in args:
		print (text, file=sys.stderr)

# Dates represented as numbers in graph
# Assumption that there are two constants
# SystemDays = number of days we've been running for
# TotalDays = number of days represented in graph
# AdjustedDays = (Days + SystemDays) % TotalDays gives you actual days
# This adds AdjustedDays to today's date to get the flight date
# ADJUSTED DAYS NOT USED IN PRACTICE
def get_date(days):
	timeNow = datetime.datetime.now()
	t = timeNow + datetime.timedelta(days=days)
	return t.strftime('%d/%m/%Y')
	
	
from abc import ABCMeta, abstractmethod
class Node(object):
	
	def __init__(self, left = None, right = None):
		self.left = left
		self.right = right
		
	
	def preorder():
		pass

class Market(object):
	
	__metaclass__ = ABCMeta
	
	def __init__(self, location, name):
		self.location = location
		self.name = [n.strip() for n in name.split(',')]
		self.number = None
		
	def market_names():
		pass
		
class Start(Market, Node):

	def __init__(self, location, name, date, day):
		Market.__init__(self, location, name)
		self.date = date
		self.day = day
		
	def market_names(self):
		pass
		
		
class Flight(object):
	
	def __init__( self, flight):
	
		self.departure = flight['market']
		self.arrival = flight['destination']
		self.cost = flight['cost']
		self.date = get_date(flight['day'])
		
		
	def html_list_element(self):
		html = "<li>{date}: {out} - {inn} \xe2\x82\xac{cost}</li>"
		return html.format(date=self.date, out=self.departure, inn=self.arrival, cost=self.cost)
		
class Trip(object):

	def __init__( self, trip ):
		self.flights = [ Flight (f) for f in trip ]
		self.cost = sum (flight.cost for flight in self.flights)
		
		# start date should be the date of first flight
		# end date should be the date of the last flight
		self.start, self.end = None, None
		
		for flight in self.flights:
			if not self.start:
				self.start = flight.date
				
			self.end = flight.date
			
		self.html = self.html_list()
		
	# Flight objects can produce a list items
	# Scaffold a html list and call the list item on each Flight
	# Return as Markup to avoid autoescaping
	def html_list(self):
		from flask import Markup
		flights_html = "\n\t\t".join(flight.html_list_element() for flight in self.flights)
		html = "<br/>Cost: \xe2\x82\xac" + str(self.cost) + "<br/><ul>" + flights_html + "\n\t</ul>"
		return Markup(html)

def create_statement(start, stops, destination, inOrder = True):
	"""
		start: where the trip begins
		stops: other places where the trip stops
		destination: the last stop before returning
		return_flight: add flight back to start from destination if exists or last stop processed
	"""
	
	return_flight = destination[-1]
	processed_statements = []
	
	# start_staement is the cypher statement that finds the starting Airport
	# airport_codes is needed when there are multiple starting Airports
	values = cypher_statement_start(*start)
	start_statement, where_statement, airport_codes = values
	
	start_and_where_statement = start_statement
	
	if where_statement:
		start_and_where_statement = start_and_where_statement  + '\n' + where_statement

	# statements find the relevant markets
	# gather all airports in processed statements and connect them
	# we use all_tuples to keep track of starting parameters
	# Big hint that the wrong data structure was used here
	# Having to keep around the data after it is used suggest objects
	processed_statements.append(start_and_where_statement)
	all_tuples = [start]

	# stop is a tuple of four parameters
	# only the first two are relevant for finding airports
	# stop[0] is Continent, Country, Region, City, or Airport
	# stop[1] is the name
	for index, stop in enumerate(stops, start = 1):
				  
		s = cypher_statement_stop(stop[0], stop[1], index)
		p( "NEW STATEMENT IN c_s", s )
								  
		processed_statements.append( s) 
		all_tuples.append(stop)

	# destination is a stop but on a return trip we go back to start from here
	if destination:
		processed_statements.append( cypher_statement_stop(destination[0], destination[1], len(processed_statements)  ))
		all_tuples.append(destination)
		
	if return_flight:
		p("\n\nRETURN\nRETURN\nRETURN\n\n")
		return_statement = cypher_statement_stop(start[0],start[1], len(processed_statements) )
		p("\n\nRETURN\nRETURN\nRETURN\n\n", return_statement)
		processed_statements.append(return_statement)
		
	
	# generate the pairs (1,2), (3,4), (5,6), etc
	# going from odd to even is a flight
	# going from even to odd finds the next market i.e. the trip between flights
	pairs = ((x*2-1,x*2, statement) for x, statement in enumerate(processed_statements))

	statement = "MATCH  "
	flights = []

	for index, pair in enumerate(pairs):
		
		early, late, ps = pair
		
		p( (index, early, late, ps ) )
		flash(all_tuples[index-1])
		
		if index >= 2: ## FIND NEW MARKET
			prev = early - 1
			duration, location = all_tuples[index-1][2:4]
			
			p( "WE NEED A NEW MArKET" )
			p( duration, location )
			
			market1 = "(ad" + str(early-1) + ") "
			next_market = " - [:NEXT_MARKET {days_between: " + str(duration) + "}] -> "
			market2 = "(ad" + str(early) + ": AirportDay) "
			
			if not location or location == 'Airport':
				
				add = market1 + next_market + market2
				p( "ADD MARKET", add )
				statement = statement + "\nMATCH " + add
				
			else:
				# match day
				next_day = market1 + next_market + " (:Date) <- [:HAS_DAY] - "
				marketAirport = market2 + "- [ha1:HAS_AIRPORT] -> (:Airport) "
				location = " - [ic1:IN_{0}] -> () <- [ic2:IN_{0}] - () <- [ha2:HAS_AIRPORT] - ".format(location.upper())
				marketAirportLocation = marketAirport + location + market1
				flash (marketAirport)
				flash (marketAirportLocation)
				statement = statement + "\nMATCH " + next_day + marketAirportLocation
				flash (statement)
				# (market) - [HAS_DAY] -> (Date) <- [HAS_DAY] - (market2 ) - [HAS_AIRPORT] - (airport) - (HAS_lOCATION)
				
			
		if index >= 1: ## Connect Flight
			p( "WE NEED TO ADD FLIGHT", processed_statements[index] )
			market = "(ad" + str(early) + ") "
			statement = statement + "\nMATCH " + market
			flight = "f" + str(index)
			flights.append(flight)
			
			try:
				statement = statement + " - [" + flight + ":FLIGHT] -> " + processed_statements[index]
			except:
				next_market_name = " (ad" + str(late) + ") "
				find_airport = " - [:HAS_AIRPORT] -> (airport{number}: Airport {{ {location} : '{name}' }} )"
				find_airport = find_airport.format(number=index, location=start[0].lower(), name=start[1][0])
				statement = statement + " - [" + flight + ":FLIGHT] -> " + next_market_name + find_airport
				
				#raise ValueError("Concatenation Error")
			
			# if index is 1 and we have other starts then need to match them here as well
			if airport_codes:
				if index == 1:
					for code in airport_codes:
						#(ad1_b) - [f1_b:Flight] - (ad2)
						flight = "f" + str(index) + "_"+ code
						flights.append(flight)
						statement = statement + ",\n(ad2) <- [f1_{0}:FLIGHT] - (ad1_{0})".format(code)
					
				elif all_tuples[index-1][-1] == True:
					for windex, code in enumerate(airport_codes, start=1):
						flight = "f" + str(index) + "_"+ code
						flights.append(flight)
						flight_statement =  ",\n{1} - [f{3}_{0}:FLIGHT] -> (ad{2}_{0}) ".format(code,market,late, index)
						find_airport = " - [:HAS_AIRPORT] -> (airport{number}_{code}: Airport {{ {location} : '{name}' }} )"
						find_airport = find_airport.format(number=index, location=start[0].lower(), name=start[1][windex], code=code)
						
						statement = statement + flight_statement + find_airport
		else:
			statement = statement + processed_statements[index]
			p ("UPDATED STTEMENT " + statement)
			
	statement = statement + "\nRETURN " + ", ".join( flights )
	flash(statement)		
	
	statement = statement + "\n ORDER BY " + " + ".join(f+".cost" for f in flights) + " ASC"
	
	p("\nORDER BY " + " + ".join(f+".cost" for f in flights) + " ASC")
	
	
	
	p( "\nRETURN " + ", ".join( flights ) )
			
	p("\n--------------",statement, "\n--------------\n")
		
	return graph.run(statement)

	
def cypher_statement_stop(location, name, stop_number, codes = None):
	"""
		Example:
		(ad2:AirportDay) - [:HAS_AIRPORT] ->
	"""
	no = str(stop_number*2)
	statement = None
	if isinstance(name, unicode) or len(name) == 1:
		if len(name) == 1:
			name = name[0]
		airport_day = "(ad" + no + ":AirportDay)"
		airport = "(:Airport {" +location.lower() +": '"+ name +"' })"
		statement = airport_day + "  - [:HAS_AIRPORT] -> " + airport  
	else:
		p("\n\n\n\nCSS PRINT NAME\n\n\n\n", type(name))
		
		
	return statement

def cypher_statement_start(location, names, date, day):
	"""
		location: airport, city, region, country, or continent
		names: list of names of type location e.g for Country -> France, Spain, Belgium
		date: narrow down flight dates
		day: modulo 7 operations where Monday is remainder 1
	"""
	
	
	location = location.lower()
	if not location or len (names) < 1 :
		raise ValueError("Must have a location and a name!")
		
	airport_codes = []
	airport_iter = iter('abcdefghijklmnop')
        
	statement = """ (airport1: Airport {{ {location} : '{name}' }} ) <- [:HAS_AIRPORT] - (ad1:AirportDay)""".format(location=location, name=names[0])
	
	for name in names[1:]:
		code = airport_iter.next() # get a letter for different airport
		addition = ", \n(ad1) - [:HAS_DAY] -> () <- [:HAS_DAY] - (ad1_{0}:AirportDay) - [:HAS_AIRPORT] -> ".format(code)
		add_airport = "(airport1_{0}:Airport {{{1} : '{2}'}})".format(code, location, name)
		statement = statement + addition + add_airport
		airport_codes.append(code)
	
	p("CURRENT STATEMENT")
	p(statement)
	p("DATE", date)
	
	ret =  (statement, airport_codes)
	
	p("CSS", ret)
    
	where = None
    
	if type(date) == list and type(date[0]) == int :
		data_type = type(date[1])
		if  data_type == int:
			where = 'WHERE ad1.day >= {date1} AND ad1.day <= {date2}'.format(date1=min(date), date2=max(date))
		elif date[1] is None:
			where = 'WHERE ad1.day = {date}'.format(date=date[0])
		elif date[1] in ['<=','>=','=']:
			where = 'WHERE ad1.day {sign} {date}'.format(date=date[0], sign=date[1])
		else:
			raise ValueError('Invalid sign type ' + str(date[1])) 
	else:
		if not date is None and not day:
			raise ValueError('Invalid date type ' + str(date))
		else:
			where = 'WHERE ad1.day % 7 = {day}'.format(day=day)
        
	
		
	ret =  (statement, where, airport_codes)
		
	

	return ret

	
def get_malaga():
	query= """
	MATCH (a:Aiport)
	WHERE a.name = 'Malaga'
	RETURN *
	"""
	flash("In get malaga query")

	return graph.find("Airport")

