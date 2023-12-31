

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'
   
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(300))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(250))
    genres = db.Column(db.ARRAY(db.String()))
    shows = db.relationship('Show', backref='venue', lazy=True)


    def __repr__ (self):
       return f'<Venue id:{self.id} name:{self.name} city:{self.city} state:{self.state} address:{self.address} phone:{self.phone} image_link:{self.image_link} facebook_link:{self.facebook_link} website_link:{self.website_link} seeking_talent:{self.seeking_talent} seeking_description:{self.seeking_description} genres{self.genres}> '
    


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__ (self):
       return f'<Artist id:{self.id} name:{self.name} city:{self.city} state:{self.state} phone:{self.phone} genres:{self.genres} image_link:{self.image_link} facebook_link:{self.facebook_link} website_link:{self.website_link} seeking_venue:{self.seeking_venue} seeking_description{self.seeking_description}> '
    

class Show(db.Model):
   __tablename__ = 'show'
   id = db.Column(db.Integer, primary_key = True)
   start_time = db.Column(db.DateTime, nullable=False)
   artist_id = db.Column(db.Integer, db.ForeignKey(
      'artist.id'), nullable=False)
   venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
   

   def __repr__(self):
      return f'<Show id:{self.id},start_time:{self.start_time}, artist_id:{self.artist_id}, venue_id:{self.venue_id} >'
   
 
   