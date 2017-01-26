from __future__ import print_function
from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
from flask import flash
import os
import uuid
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')

graph = Graph(url + '/db/data/', username=username, password=password)

def p(*args):
	for text in args:
		print (text, file=sys.stderr)
		
class Flight(object):
	
	def __init__( self, flight):
	
		self.departure = flight['market']
		self.arrival = flight['destination']
		self.cost = flight['cost']
		self.day = flight['day']
		
	def html_list_element(self):
		html = "<li>{day}: {out} - {inn} {cost}</li>"
		return html.format(day=self.day, out=self.departure, inn=self.arrival, cost=self.cost)
		
class Trip(object):

	def __init__( self, trip ):
		self.flights = None
		
	def html_list():
		html = "<ul>" + "\n\t\t".join(flight.html_list_element for flight in self.flights) + "\n\t</ul>"

def create_statement(start, stops, destination, inOrder = True, return_flight = True):
	"""
		start: where the trip begins
		stops: other places where the trip stops
		destination: the last stop before returning
		inOrder: boolean, visit stops in defined order
		return_flight: add flight back to start from destination if exists or last stop processed
	"""
	
	
	processed_statements = []
	
	# start_staement is the cypher statement that finds the starting Airport
	# airport_codes is needed when there are multiple starting Airports
	values = cypher_statement_start(*start)
	p("VALUES", len(values))
	p(values)
	
	start_statement, airport_codes = values

	processed_statements.append(start_statement)
	all_tuples = [start]


	for index, stop in enumerate(stops, start = 1):
				  
		s = cypher_statement_stop(stop[0], stop[1], index)
		p( "NEW STATEMENT IN c_s", s )
								  
		processed_statements.append( s) 
		all_tuples.append(stop)

	if destination:
		processed_statements.append( cypher_statement_stop(destination[0], destination[1], len(processed_statements)  )) 
		
	
		
	pairs = ((x*2-1,x*2, statement) for x, statement in enumerate(processed_statements))

	statement = ""
	flights = []

	for index, pair in enumerate(pairs):
		
		early, late, ps = pair
		
		p( (index, early, late, ps ) )
		
		if index >= 2: ## FIND NEW MARKET
			prev = early - 1
			duration, location = all_tuples[index-1][2:]
			
			p( "WE NEED A NEW MArKET" )
			p( duration, location )
			
			if not location or location == 'Airport':
				market1 = "(ad" + str(early-1) + ") "
				market2 = "(ad" + str(early) + ": AirportDay)"
				add = market1 + " - [:NEXT_MARKET {days: " + str(duration) + "}] -> " + market2
				p( "ADD MARKET", add )
				statement = statement + "\nMATCH " + add
			
		if index >= 1: ## Connect Flight
			p( "WE NEED TO ADD FLIGHT", processed_statements[index] )
			statement = statement + "\nMATCH (ad" + str(early)
			flight = "f" + str(index)
			flights.append(flight)
			statement = statement + ") - [" + flight + ":FLIGHT] -> " + processed_statements[index]
			
			# if index is 1 and we have other starts then need to match them here as well
			if index == 1 and airport_codes:
				for code in airport_codes:
					#(ad1_b) - [f1_b:Flight] - (ad2)
					statement = statement + ",\n(ad2) <- [f1_{0}:FLIGHT] - (ad1_{0})".format(code)
			
		else:
			statement = statement + processed_statements[index]
			p ("UPDATED STTEMENT " + statement)
			
	statement = statement + "\nRETURN " + ", ".join( flights )
			
	statement = statement + "\n ORDER BY " + " + ".join(f+".cost" for f in flights) + " ASC"
	
	p("\nORDER BY " + " + ".join(f+".cost" for f in flights) + " ASC")
	
	
	
	p( "\nRETURN " + ", ".join( flights ) )
			
	p("\n--------------",statement, "\n--------------\n")
		
	return graph.run(statement)

def cypher_statement_stop(location, name, stop_number):
	no = str(stop_number*2)
	airport_day = "(ad" + no + ":AirportDay)"
	airport = "(:Airport {" +location.lower() +": '"+ name +"' })"
	statement = airport_day + "  - [:HAS_AIRPORT] -> " + airport  
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
        
	statement = """MATCH (airport1: Airport {{ {location} : '{name}' }} ) <- [:HAS_AIRPORT] - (ad1:AirportDay)""".format(location=location, name=names[0])
	
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
		if not date is None:
			raise ValueError('Invalid date type ' + str(date))
        
	if where:
		statement = statement  + '\n' + where
		
	ret =  (statement, airport_codes)
		
	

	return ret

def get_todays_recent_posts():
	query = '''
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    WHERE post.date = {today}
    RETURN user.username AS username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT 5
    '''
	
	return graph.run(query, today=date())
	
def get_malaga():
	query= """
	MATCH (a:Aiport)
	WHERE a.name = 'Malaga'
	RETURN *
	"""
	flash("In get malaga query")

	return graph.find("Airport")

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')
