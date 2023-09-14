# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import collections
import collections.abc

collections.Callable = collections.abc.Callable
from markupsafe import Markup
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from wtforms import StringField
from models import db, Venue, Artist, Show


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)  
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


# This route is displaying the venues and their scheduled performances, arranged by city and state.

@app.route("/venues")
def venues():
    data = []  # venue data

    venues_by_city_state = {}  # organizing venues by city and state.
    places = Venue.query.all() 

    # creating a data structure where venues are organized by its own city and state: 

    for place in places:
        key = (place.city, place.state)
        if key not in venues_by_city_state:
            venues_by_city_state[key] = {
                "city": place.city,
                "state": place.state,
                "venues": [],
            }

    date = datetime.now()
    shows_by_venue = {} #  store information about the new shows for each venue.
    for place in places:
        gigs = Show.query.filter_by(venue_id=place.id).all()
        num_upcoming_shows = sum(1 for gig in gigs if gig.start_time > date)
        shows_by_venue[place.id] = {
            "id": place.id,
            "name": place.name,
            "upcoming": num_upcoming_shows,
        }

    for key, venue_data in venues_by_city_state.items():
        venue_data["venues"] = [
            shows_by_venue[place.id]
            for place in places
            if (place.city, place.state) == key
        ]
        data.append(venue_data)

    return render_template("pages/venues.html", areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    #The Search_term' field's value is retrieved from the POST request's form data. 
    #The field defaults to be empty if its not filled.
    #The search_results does a case-insensitive database search for venues whose names partially match the supplied search word. 

    search_term = request.form.get('search_term', '')
    search_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()


    #for loop through each venue in the search_results list. 
    #then searche the database for new shows of each venue,
    #where the start time of the show is greater than the current date and time to get the number of shows for each Venue.
    #Each venue receives a dictionary with the keys "id," "name," and "num_upcoming_shows" that is created and added to the data list.

    data = []
    for venue in search_results:
        num_upcoming_shows = Show.query \
            .filter(Show.venue_id == venue.id) \
            .filter(Show.start_time > datetime.now()) \
            .count()

        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows,
        })

    #A response with a dictionary name that contains the number of search results and a list of venue ifno. 
    #The count indicates how many venues matches the search.

    response = {
        "count": len(search_results),
        "data": data
    }
    
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    if not venue:
        return render_template('errors/404.html')

    # two different queries to obtain details regarding upcoming shows (newShows) and previous shows (oldShows) for the selected venue.
    # newshows_q fetches the new shows by querying the database for shows associated with the venue where the show's start time is greater than the current date and time.
    # and oldshows_q does the same but where the show's start time is less than the current date and time. 

    date_now = datetime.now()
    newshows_q = (
        db.session.query(Show)
        .join(Artist)
        .filter(Show.venue_id == venue_id, Show.start_time > date_now)
        .all()
    )

    oldshows_q = (
        db.session.query(Show)
        .join(Artist)
        .filter(Show.venue_id == venue_id, Show.start_time < date_now)
        .all()
    )

    #after the show data has been fetched, its converted into lists of dictionaries (oldshows and newshows), 
    # each of them contains information about the artist.

    
    oldshows = [
        {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for show in oldshows_q
    ]

    newshows = [
        {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for show in newshows_q
    ]

    #Venue data
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": oldshows,
        "upcoming_shows": newshows,
        "past_shows_count": len(newshows),
        "upcoming_shows_count": len(newshows),
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)



@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form) #flask-wtf form.
    
    # creating a new Venue.
    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )

        db.session.add(venue)
        db.session.commit()
        flash("Venue " + request.form["name"] + " was successfully added!")

    except Exception as e:
        db.session.rollback()
        flash("Error: " + str(e))  # displays what's the error exactly

    finally:
        db.session.close()


    return render_template("pages/home.html")




#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
   artists = Artist.query.all()
   return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    # The same explanation as searching for a venue.
    # i used the same code for both Artists and Venues. 

    search_term = request.form.get('search_term', '')
    search_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    data = []
    for artist in search_results:
        num_upcoming_shows = Show.query \
            .filter(Show.artist_id == artist.id) \
            .filter(Show.start_time > datetime.now()) \
            .count()

        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows,
        })

    response = {
        "count": len(search_results),
        "data": data
    }
    
    return render_template('pages/search_artists.html', results=response, search_term=search_term)

    
     


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    #also the same code i used for Venue, i use it here for the artists.
  
    artist = Artist.query.get(artist_id)

    if not artist:
        return render_template('errors/404.html')

    
    date_now = datetime.now()
    oldshows_q = (
        db.session.query(Show)
        .join(Venue)
        .filter(Show.artist_id == artist_id, Show.start_time < date_now)
        .all()
    )

    newshows_q = (
        db.session.query(Show)
        .join(Venue)
        .filter(Show.artist_id == artist_id, Show.start_time > date_now)
        .all()
    )

    oldshows = [
        {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for show in oldshows_q
    ]

    newshows = [
        {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for show in newshows_q
    ]

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": oldshows,
        "upcoming_shows": newshows,
        "past_shows_count": len(oldshows),
        "upcoming_shows_count": len(newshows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    # makes a database query to find the artist whose artist_id is given.
    # A 404 error is returned if no artists matching that ID are found.
    artist = Artist.query.get(artist_id)

    try:
        form = ArtistForm(request.form) # creates an instance of the ArtistForm form object. 
        form.populate_obj(artist) # to update the artist's info

        db.session.commit()
        flash("Successful.")
    except Exception as e:
         db.session.rollback()
         flash("Error: " + str(e))
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    
    form = VenueForm() 
    venue = Venue.query.get(venue_id)
    

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    # the same code i used in edit artist, but this block is for editing the venue.
    
    venue = Venue.query.get(venue_id)

    try:
        form = VenueForm(request.form)
        form.populate_obj(venue)

        db.session.commit()
        flash("Successful.")
    except Exception as e:
         db.session.rollback()
         flash("Error: " + str(e))
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))



#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    form = ArtistForm(request.form)

    try:
      
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
        )

        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully added!")


    except Exception as e:
        
        db.session.rollback()
        flash("Error: " + str(e))
    finally:
        db.session.close()


    return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    #by using JOIN to join shows,venues and artists and fetch the info, the all() fetches all the the matching records.
    shows_q = db.session.query(Show).join(Artist).join(Venue).all()

    data = [] #shows info 

    #by using for loop, to take info about venue,artist and show 
    for show in shows_q:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S') #specific date and time
        })

    return render_template('pages/shows.html', shows=data)


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    #same creating code for artists and venues: 
    
    form = ShowForm(request.form)

    try:
        show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
        db.session.add(show)
        db.session.commit()
        flash("the show was successfully added!")

    except Exception as e:
      db.session.rollback()
      flash("Error: " + str(e))

    finally:
        db.session.close()

    return render_template('pages/home.html')



@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
