import streamlit as st
import pandas as pd

class Movie:
    def __init__(self, movieID, title, genre, duration, image):
        self.movieID = movieID
        self.title = title
        self.genre = genre
        self.duration = duration
        self.image = image
        self.ratings = []
        self.views = 0
    def avg_rating(self):
        return sum(self.ratings) / len(self.ratings) if self.ratings else 0

class User:
    def __init__(self, userID, username, preferences=None,watch_history=None,ratings=None):
        self.userID = userID
        self.username = username
        self.preferences = preferences or []
        self.watch_history = watch_history or []
        self.ratings = ratings or {}
    def watch_movies(self,movie):
        if movie.movieID not in self.watch_history:
            self.watch_history.append(movie.movieID)
        movie.views +=1
    def rate_movies(self, movie, rate):
        if movie.movieID in self.ratings:
            old = self.ratings[movie.movieID]
            if old in movie.ratings:
                movie.ratings.remove(old)
        self.ratings[movie.movieID] = rate
        movie.ratings.append(rate)
        if movie.genre not in self.preferences:
            self.preferences.append(movie.genre)
    def to_csv(self):
        prefer = ";".join(self.preferences)
        history = ";".join(self.watch_history)
        ratings = ";".join([f"{k}:{v}" for k, v in self.ratings.items()])
        return f"{self.userID},{self.username},{prefer},{history},{ratings}\n"

class Recommendation:
    def create_rec(self, user, movies, top_n=5):
        return sorted(
            [m for m in movies if m.movieID not in user.watch_history],
            key=lambda m: (
                    (3 if m.genre in user.preferences else 0) +
                    (m.avg_rating() * 2) +
                    min(m.views / 5, 5)),
            reverse=True)[:top_n]

## LOAD MOVIE LIBRARY
def load_movies(file):
    movies = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(",", 4)
            movies.append(Movie(parts[0], parts[1], parts[2], int(parts[3]), parts[4]))
    return movies

def load_users(file):
    users = {}
    try:
        with open(file, "r") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split(",", 4)
                userID = parts[0]
                username = parts[1]
                prefer = parts[2].split(";") if parts[2] else []
                history = parts[3].split(";") if parts[3] else []
                ratings = {}
                if len(parts) > 4 and parts[4]:
                    for r in parts[4].split(";"):
                        m_id, rate = r.split(":")
                        ratings[m_id] = int(rate)
                users[username] = User(userID, username, prefer, history, ratings)
    except FileNotFoundError:
        pass
    return users


def save_users(file, users):
    with open(file, "w") as f:
        f.write("userID,username,preferences,watch_history,ratings\n")
        for user in users.values():
            f.write(user.to_csv())


def update_movie_data(movies, users):
    movie_data = {m.movieID: m for m in movies}
    for m in movies:
        m.ratings = []
        m.views = 0
    for user in users.values():
        for m_id in user.watch_history:
            if m_id in movie_data:
                movie_data[m_id].views += 1
        for m_id, rate in user.ratings.items():
            if m_id in movie_data:
                movie_data[m_id].ratings.append(rate)


## CALL .TXT FILES
if "movies" not in st.session_state:
    st.session_state.movies = load_movies("movie library.txt")

if "users" not in st.session_state:
    st.session_state.users = load_users("users.txt")


update_movie_data(st.session_state.movies, st.session_state.users)

if "user" not in st.session_state:
    st.session_state.user = None

if "needs_preferences" not in st.session_state:
    st.session_state.needs_preferences = False

recom = Recommendation()

#### GUI INTERFACE
## LOG IN
st.title("Movie Streamer")

if not st.session_state.user:
    tab1, tab2, tab3 = st.tabs(["Login", "Register","Admin"])

    with tab1:
        username = st.text_input("Username")
        if st.button("Login"):
            if username in st.session_state.users:
                st.session_state.user = st.session_state.users[username]
                if not st.session_state.user.preferences:
                    st.session_state.needs_preferences = True
                st.rerun()
            else:
                st.warning("User not found")

    with tab2:
        new_user = st.text_input("New Username")
        if st.button("Register"):
            if new_user and new_user not in st.session_state.users:
                uid = f"U{len(st.session_state.users)+1}"
                user = User(uid, new_user, [], [], {})
                st.session_state.users[new_user] = user
                st.session_state.user = user
                st.session_state.needs_preferences = True
                save_users("users.txt", st.session_state.users)
                st.rerun()
            else:
                st.warning("Invalid username")

    with tab3:
        admin_pass = "admin2026"
        passwd = st.text_input("Password",type="password")
        if passwd != admin_pass:
            st.warning("Invalid password")
        else:
            st.success("Welcome to Admin Mode!")




## NEW REGISTER -> INPUT PREFERENCE
if st.session_state.user and st.session_state.needs_preferences:
    user = st.session_state.user

    st.title("What is your favourite genre?")

    genres = list({m.genre for m in st.session_state.movies})
    selected = st.multiselect("Select Genres", genres)

    if st.button("Save Selection"):
        if selected:
            user.preferences = selected
            save_users("users.txt", st.session_state.users)
            st.session_state.needs_preferences = False
            st.success("Preferences saved!")
            st.rerun()
        else:
            st.warning("Select at least one genre!")
    st.stop()

## MAIN PAGE
#trending
if st.session_state.user:
    user = st.session_state.user

    st.header("Trending, Must Watch!")
    trending = sorted(st.session_state.movies, key=lambda m: m.views, reverse=True)[:3]
    cols = st.columns(3)
    for i, m in enumerate(trending):
        with cols[i % 3]:
            st.image(m.image)
            st.markdown(f"**{m.title}**")
            st.caption(f"{m.genre} • {m.duration} min")
            st.write(f"⭐ {m.avg_rating():.1f}")
#top picks
    if user.preferences:
        st.header("Curated Just For You:")
        top_movies = recom.create_rec(user, st.session_state.movies)
        cols = st.columns(3)
        for i, m in enumerate(top_movies):
            with cols[i % 3]:
                st.image(m.image)
                st.markdown(f"**{m.title}**")
                st.caption(f"{m.genre} • {m.duration} min")
                st.write(f"⭐ {m.avg_rating():.1f}")
#search
    st.header("Search Movies")
    keyword = st.text_input("Search by title keyword")
    genre = st.selectbox("Filter by genre", ["All"] + list({m.genre for m in st.session_state.movies}))

    results = [
        m for m in st.session_state.movies
        if (keyword.lower() in m.title.lower() if keyword else True)
           and (m.genre == genre if genre != "All" else True)]
    st.subheader("Results:")
    for m in results:
        st.write(f"{m.title} ({m.genre}) ⭐ {m.avg_rating():.1f} | Views: {m.views}")
        if st.button("Select", key=f"browse_{m.movieID}"):
            st.session_state.selected = m
#rating
    if "selected" in st.session_state:
        m = st.session_state.selected
        st.subheader(f"Rate: {m.title}")
        rating = st.slider("Rating", 1, 5, 3)

        if st.button("Submit Rating"):
            user.watch_movies(m)
            user.rate_movies(m, rating)
            save_users("users.txt", st.session_state.users)
            st.success("Thank you for rating this movie!")
            st.rerun()
#recommendation
    st.header("Recommended")
    if st.button("More Recommendations"):
        recs = recom.create_rec(user, st.session_state.movies)
        if recs:
            for m in recs:
                st.write(f"{m.title}")
        else:
            st.warning("Rate movies or add more genres to your preferences!")
            st.subheader("Manage Movie Library")
            st.write("You May Add, edit, or Remove Movies")

#Insights
df = pd.DataFrame([{
    "title": m.title,
    "genre": m.genre,
    "views": m.views,
    "avg_rating": m.avg_rating()} for m in st.session_state.movies])

st.subheader("Highest Rating Movies")
top_rated = df.sort_values("avg_rating", ascending=False).head(5)
st.bar_chart(top_rated.set_index("title")["avg_rating"])

#ADMIN PAGE
if st.session_state.user:
    admin = st.session_state.user

def save_movies(file, movies):
    with open(file, "w", encoding="utf-8") as f:
        f.write("movie_id,title,genre,duration,image\n")
        for m in movies:
            f.write(f"{m.movie_id},{m.title},{m.genre},{m.duration},{m.image}\n")

new_movieID = st.text_input("Movie ID", key="admin_movieID")
new_title = st.text_input("Title", key="admin_title")
new_genre = st.text_input("Genre", key="admin_genre")
new_duration = st.number_input("Duration", min_value=1, step=1, key="admin_duration")
new_image = st.text_input("Image File", key="admin_image")

if st.button("Add Movie"):
    if new_movieID and new_title and new_genre:
        movie = Movie(new_movieID, new_title, new_genre, new_duration, new_image)
        st.session_state.movies.append(movie)
        save_movies("movie library.txt", st.session_state.movies)
        st.success(f"Added {new_title}")
    else:
        st.warning("Unable to add new Movie")

st.subheader("Edit / Remove Movie")
movieID = [m.movieID for m in st.session_state.movies]
selected_movieID = st.selectbox("Select Movie", [""] + movieID, key="admin_select_movie")
if selected_movieID:
    movie = next((m for m in st.session_state.movies if m.movie_ID == selected_movieID), None)
    if movie:
        movie.title = st.text_input("Title", movie.title, key="admin_edit_title")
        movie.genre = st.text_input("Genre", movie.genre, key="admin_edit_genre")
        movie.duration = st.number_input("Duration", value=movie.duration, min_value=1,
                                         key="admin_edit_duration")
        movie.image = st.text_input("Image URL", movie.image, key="admin_edit_image")

        if st.button("Save Movie Changes"):
            save_movies("movie library.txt", st.session_state.movies)
            st.success(f"Saved {movie.title}")

        if st.button("Remove Movie"):
            st.session_state.movies = [m for m in st.session_state.movies if m.movie_id != movie.movie_id]
            save_movies("movie library.txt", st.session_state.movies)
            st.success(f"Removed {movie.title}")






