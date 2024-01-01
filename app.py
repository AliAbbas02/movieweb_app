from flask import Flask, jsonify, abort, request, render_template, json, session, redirect, url_for
from data_managment.json_data_manager import JSONDataManager
import requests


app = Flask(__name__)
app.secret_key= 'codingisfunrun'

#fetch the data as soon as the API is accessed
data_manager:JSONDataManager = JSONDataManager('movieweb_app\data\movies.json')

#fetch deleted user id files so we can utalize them 
deleted_ids_file_path:str = 'movieweb_app\data\deleted_ids.json'
with open(deleted_ids_file_path) as f:
    deleted_ids:list = sorted(json.load(f))

@app.errorhandler(404)
def not_found(error):
    return jsonify('user not found with provided id... Please Try Again !!!')

@app.errorhandler(400)
def bad_request(error):
    return jsonify('important fields missing, Please check and try again.')

@app.route('/', methods=['GET'])
def home():
    if request.method == 'GET':
        users:dict = data_manager.get_all_users()
        all_movies:list = [ movies for _, movies in users.items()]
        #images that will be shown on homepage background
        images:list = all_movies[:101]
        return render_template('index.html', movie_iamges = images)


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        id:int = request.form.get('id',)
        password:str = request.form.get('password')
        #vallidating user if it exists in database
        if data_manager.validate_user(id, password):
            #if user exists make a session key for its id 
            session['id']: dict = str(id)
            return redirect(url_for('dashboard.html'))
        else:
            return redirect(url_for('login')), 404
    
    return render_template('login.html')

        

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'id' in session:
        return render_template('dashboard.html')
    #if user tried to access this route without logging in
    return redirect(url_for(login))



def listing_data(data) -> list:
    '''a function that takes dicts of dict and converts them 
    into list of dicts and returns ids and names
    Args:
        data:dict dictionary of dicts
    '''
    users:list = []
    for _, user_info in data.items():
        users.append({user_info['name']})
    return users 

@app.route('/users')
def list_users():
    users:dict = data_manager.get_all_users()
    if users == {}:
        return jsonify('no users registered in database !!!')
    #return users as list of all users
    return render_template('all_users.html', users=listing_data(users))


def update_users_jsonfile(new_data) -> None:
    '''a function that updates the changed data in json storage file
    Args:
        new_data:dict data modified/changed by current user'''
    #file path to json storage of our app
    filepath:str = 'movieweb_app\data\movies.json'
    with open(filepath, 'w') as f:
        json.dump(new_data, f, indent=4)


def update_deleted_ids(used_id) -> None:
    '''a function that updated the deleted ids file after
    alloting an id to new user
    Args:
        user_id:int id that is assinged to new user
    '''
    #removes the first occuring of id 
    deleted_ids.remove(used_id)
    with open(deleted_ids_file_path, 'w') as f:
        json.dump(deleted_ids, f, indent= 4)


def update_data(username, password, movies) -> None:
    '''a function that gets the info of new user and its favorite
    movies if any and updates data in json storage file
    Args:
        username:str name of the user
        movies:dict movie chosen by user and fetched from online Api
        '''

    all_user:dict = data_manager.get_all_users()

    #checking if there is an id in deleted ids and if users are not empty 
    if deleted_ids != [] and all_user != {}:
        #allocate the first id in deleted id to new user
        all_user[str(deleted_ids[0])] = {'name': username,\
                                        'movies': movies,
                                         'password': password }
        #update deleted file
        update_deleted_ids(deleted_ids[0])
    else:
        #if deleted ids file has no id to allocate give biggest id user 
        # added one to new user
        user_ids: list = sorted(map(int,all_user.keys()))
        new_id_for_user:int = user_ids[-1] + 1
        all_user[str(new_id_for_user)] = {'name': username,\
                                        'movies' : movies,
                                        'password': password}

    update_users_jsonfile(all_user)


    
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        #check if all the fields are passed in form data
        if 'username' not in request.form or 'password' not in request.form:
            abort(400)
        username = request.form.get('username')
        password = request.form.get('password')
        movies = request.form.get('movies', default= {})

        #create user in json storage file 
        update_data(username, password, movies)
        #redirect to login page once the user is created
        return redirect(url_for('login')),201
    #if any field missing or a get request render the register page
    return render_template('register.html')

 

@app.route('/users/<int:user_id>')
def user_movies(user_id) -> list:
    #if user exists with the id and also user is logged in 
    if 'id' in session:
        try:
            movies:dict = data_manager.get_user_movies(str(user_id)) 
        #if user with id doesnot exists send out an error message
        except KeyError:
            abort(404)
        #if user has no movies    
        if movies == {}:
            return  jsonify('this user has no favorite movies')
        #converting dict of movie dicts into list of movie dicts
        movies:list = [{movie : movie_data} for movie, movie_data\
                in movies.items()]
        return render_template('user_movies.html', movies=movies)
    else:
        return redirect('login'), 400


def search_movie_online(movie)-> ({}, {}, None):
    '''a function that retuns movie as a dict if found on online API
    else returns an empty dict, it returns None if cannot connect to 
    server
    Args:
        movie:str movie requested by user'''
    API_KEY:str = 'd322e1a0'
    URL:str= 'http://www.omdbapi.com/'
    params:dict= {'t': movie, 'apikey': API_KEY }
    try:
        response:dict = requests.get(URL, params=params).json()
        if response['Response'] == 'True':
            title:str = response['Title']
            year:int = int(response['Year'])
            rating:float = float(response['imdbRating'])
            image_url:str = response['Poster']
            link:str = response['imdbID'] 
            country:list = response['Country']
            #add the mosvie into database
            return title, {
            'year': year, 
            'rating':rating,
            'image': image_url,
            'link': link,
            'country': country}
            
        else:
            return {} 
            #if cannot connect to server   
    except requests.exceptions.ConnectionError as e:
        return None
    


@app.route('/users/<int:user_id>/add_movie', methods=['GET','POST'])
def add_movie(user_id):
    all_users = data_manager.get_all_users()
    if 'id' in session:
        if request.method == 'POST':
            # if movie not entered by user 
            if 'movie' not in request.form:
                return jsonify('please choose a movie to add in favorites..!!'), 400
            movie_entered = request.form.get('movie').title()
            try:
                #if movie already in dfavorites
                if all_users[str(user_id)]['movies'][movie_entered]:
                    return jsonify('movie already in favorites')
            #if movie not in database search movie online 
            except KeyError:   
                title, movie = search_movie_online(movie_entered)
                #if no movie found online with the provided title
                if movie == {}:
                    abort(404)
                # if cannot connect to online movie api to fetch movie data 
                elif movie == None:
                    return jsonify('connection error please try again..!!')
                else:
                    all_users[str(user_id)]['movies'][title] = movie
                    update_users_jsonfile(all_users)
                    return jsonify('movie added to favorites'), 201
        
        return render_template('add_movie.html', user= str(user_id))
    else:
        return redirect('login')
                

@app.route('/users/<int:user_id>/update_movie/<title>', methods=['GET', 'PUT'])
def update_movie(user_id, title):
    if 'id' in session:
        try:
            movie = data_manager.get_user_movies(str(user_id)).get(title.title())
            if movie == None:
                return jsonify('movie not found in favorite movies'),404
            #use fuzzy wuzzy
            if request.method == 'GET':
                #send default values 
                return render_template('update_movie.html', data=movie)
            elif request.method == 'PUT':
                updated_values = {
                'country' : request.form.get('country', movie['country']),
                'image' : request.form.get('image', movie['image']),
                'rating' : request.form.get('rating', movie['rating']),
                'link' : request.form.get('link', movie['link']),
                'year' :request.form.get('year', movie['year'])}

                all_users = data_manager.get_all_users()
                all_users[str(user_id)]['movies'][title.title()].update(updated_values)
                update_users_jsonfile(all_users)
                return jsonify('movie succesfully updated')

        except KeyError:
            abort(404)
    else:
        return redirect('login')

@app.route('/users/<int:user_id>/delete_movie/<title>', methods=['DELETE'])
def delete_movie(user_id, title):
        if 'id' in session:
            try:
                movie = data_manager.get_user_movies(str(user_id)).get(title.title())
                if movie == None:
                    return jsonify('movie not found in favorite movies'),404
                
                all_users = data_manager.get_all_users()
                del all_users[str(user_id)]['movies'][title.title()]
                update_users_jsonfile(all_users)
                return jsonify('movie succesfully deleted')

            except KeyError:
                abort(404)
        return redirect('login')



if __name__ == '__main__':
    app.run(debug=True)