from django.shortcuts import render, redirect
import csv
from csv import writer
import os
import math
from django import template
import pandas as pd
from home.Book_recommendation_model_2 import sim_distance, get_recommendations 
from django.http import HttpResponse
from home.models import Cart, Interest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DATA_PATH = os.path.join(BASE_DIR, 'home', 'book_data2.csv')
RATINGS_PATH = os.path.join(BASE_DIR, 'home', 'ratings.csv')

register = template.Library()

@register.filter
def round_up(value):
    return int(math.floor(value))

def rated(userId, bookId):
    ratings = pd.read_csv(RATINGS_PATH, engine="python")
    print("Columns in ratings CSV:", ratings.columns)
    ratings.columns = ratings.columns.str.strip()
    
    if 'user_id' in ratings.columns and 'book_id' in ratings.columns:
        ratings = ratings[ratings["user_id"] == int(userId)]
        ratings = ratings.values.tolist()
        j = 0
        rat = 0
        flag = False
        for i in ratings:
            if i[1] == int(bookId):
                rat = ratings[j][2]
                rat = rat * 20
                flag = True
                break
            j = j + 1
        if flag:
            return [flag, rat]
        else:
            return [flag, 0]
    else:
        print("Required columns are missing in the CSV")
        return [False, 0]

def giveRating(rating, userId, bookId):
    ratings = pd.read_csv(RATINGS_PATH, engine="python")
    ratings.columns = ratings.columns.str.strip()
    
    if 'user_id' in ratings.columns and 'book_id' in ratings.columns:
        ratings = ratings[ratings["user_id"] == int(userId)]
        ratings = ratings.values.tolist()
        flag = False
        for i in ratings:
            if i[1] == int(bookId):
                flag = True
                break
        if not flag:
            row = [int(userId), int(bookId), rating]
            with open(RATINGS_PATH, 'a+', newline='') as write_obj:
                csv_writer = writer(write_obj)
                csv_writer.writerow(row)
    else:
        print("Required columns are missing in the CSV")

def recommend(bookid):
    book_description = pd.read_csv(BOOK_DATA_PATH, engine="python")
    books_tfidf = TfidfVectorizer(stop_words='english')
    book_description['book_desc'] = book_description['book_desc'].fillna('')
    book_description_matrix = books_tfidf.fit_transform(book_description['book_desc'])
    cosine_similarity = linear_kernel(book_description_matrix, book_description_matrix)
    similarity_scores = list(enumerate(cosine_similarity[bookid]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    similarity_scores = similarity_scores[1:6]
    books_index = [i[0] for i in similarity_scores]
    print(book_description['book_title'].iloc[books_index])
    viewdata = book_description.iloc[books_index].values.tolist()
    return viewdata

def product(request):
    return render(request, 'product.html')

def index(request, booktitle=None, bookauthor=None):
    if 'loginuser' in request.session:
        sameauth = {}
        data = {}
        rbooks = {}
        rbooks1 = []
        top1 = []
        mydata = pd.read_csv(BOOK_DATA_PATH, engine="python")
        top = mydata.head(20)

        ratings = pd.read_csv(RATINGS_PATH, engine="python")
        d = ratings.groupby('user_id')[['book_id', 'rating']].apply(lambda x: dict(x.values)).to_dict()

        uname = request.session["loginuser"]
        userId = request.session["userId"]

        data = ratings[ratings["user_id"] == userId]
        print(data)

        popular = mydata.sort_values(by=['book_rating'], ascending=False)
        popular = popular.head(10)
        
        if data.empty:
            print("empty")
            top = top.values.tolist()
            top1.append(top)
            sameauth["auth"] = top1
        else:
            print("not empty")
            rec_books = get_recommendations(d, userId)
            print(rec_books)
            for i in range(10):
                book_id = rec_books[i][1]
                rbooks = mydata[mydata["book_id"] == book_id]
                rbooks = rbooks.values.tolist()
                rbooks1.append(rbooks)
            
            sameauth["auth"] = rbooks1
        sameauth["auth2"] = popular.values.tolist()

        if 'viewbook' in request.POST:
            viewbookbtn = request.POST.get('viewbook') 
            id = int(viewbookbtn)
            viewdata = mydata[mydata["book_id"] == id]
            avgrating = viewdata["book_rating"]
            avgrating = int(avgrating) * 20
            viewdata = viewdata.values.tolist()
            test = rated(1, id)
            
            book_description = pd.read_csv(BOOK_DATA_PATH, encoding='latin-1')
            books_tfidf = TfidfVectorizer(stop_words='english')
            book_description['book_desc'] = book_description['book_desc'].fillna('')
            book_description_matrix = books_tfidf.fit_transform(book_description['book_desc'])
            cosine_similarity = linear_kernel(book_description_matrix, book_description_matrix)
            similarity_scores = list(enumerate(cosine_similarity[id - 1]))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
            similarity_scores = similarity_scores[1:6]
            books_index = [i[0] for i in similarity_scores]
            viewdata1 = book_description.iloc[books_index].values.tolist()
            return render(request, 'product.html', {'viewbook': viewdata, 'viewbook1': viewdata1, 'avgrating': avgrating, 'test': test})

        if 'link' in request.POST:
            rating = request.POST.get('rating')
            bookId = request.POST.get('bookId')
            test = rated(userId, bookId)
            if not test[0]:
                test[0] = True
                test[1] = rating
                giveRating(rating, userId, bookId)
            id = int(bookId)
            viewdata = mydata[mydata["book_id"] == id]
            avgrating = viewdata["book_rating"]
            avgrating = int(avgrating) * 20
            viewdata = viewdata.values.tolist()
            test = rated(1, id)
            
            book_description = pd.read_csv(BOOK_DATA_PATH, encoding='latin-1')
            books_tfidf = TfidfVectorizer(stop_words='english')
            book_description['book_desc'] = book_description['book_desc'].fillna('')
            book_description_matrix = books_tfidf.fit_transform(book_description['book_desc'])
            cosine_similarity = linear_kernel(book_description_matrix, book_description_matrix)
            similarity_scores = list(enumerate(cosine_similarity[id - 1]))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
            similarity_scores = similarity_scores[1:6]
            books_index = [i[0] for i in similarity_scores]
            viewdata1 = book_description.iloc[books_index].values.tolist()
            return render(request, 'product.html', {'viewbook': viewdata, 'viewbook1': viewdata1, 'avgrating': avgrating, 'test': test})

        if 'sbutton' in request.POST:
            viewdata1 = []
            if (request.POST.get('stype') == '0'):
                title = request.POST.get('searchbox')
                viewdata = mydata[mydata['book_title'] == title]
                viewdata = viewdata.values.tolist()
                viewdata1.append(viewdata)
                sameauth['auth'] = viewdata1
            if (request.POST.get('stype') == '1'):
                author = request.POST.get('searchbox')
                viewdata = mydata[mydata['book_author'] == author]
                sameauth['auth'] = viewdata.values.tolist()
            return render(request, 'index.html', sameauth)
        
        return render(request, 'index.html', sameauth)
    else:
        return redirect('account/login')

def wishlist(request):
    if 'loginuser' in request.session:
        viewdata = {}
        viewdata1 = []
        uname = request.session["loginuser"]
        userId = request.session["userId"]
        ratings = pd.read_csv(RATINGS_PATH, engine="python")
        books = pd.read_csv(BOOK_DATA_PATH, encoding='latin-1')
        ratings = ratings[ratings["user_id"] == userId]
        for bookID in ratings["book_id"]:
            viewdata = books[books["book_id"] == bookID]
            viewdata = viewdata.values.tolist()
            viewdata1.append(viewdata)    
        
        return render(request, 'wishlist.html', {'cartdisplay': viewdata1})
    else:
        return redirect('account/login')
