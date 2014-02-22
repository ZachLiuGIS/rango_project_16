from datetime import datetime
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from rango.bing_search import run_query


## Helper functions
def encode_url(name):
    return name.replace(' ', '_')


def decode_url(url):
    return url.replace('_', ' ')


def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    for cat in cat_list:
            cat.url = encode_url(cat.name)

    return cat_list



## Views
def index(request):
    category_list = Category.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    for category in category_list:
        category.url = encode_url(category.name)

    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list

    #### NEW CODE ####
    # Obtain our Response object early so we can add cookie information.
    response = render(request, 'rango/index.html', context_dict)

    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, we default to zero and cast that.
    #visits = int(request.COOKIES.get('visits', '0'))

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    return response


def category(request, category_name_url):

    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name = decode_url(category_name_url)

    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name}
    context_dict['category_name_url'] = category_name_url

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(name=category_name)

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages

        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category

    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass

    if request.method == 'POST':
        query = request.POST['query-category'].strip()
        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)


def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return redirect("rango:index")
        else:
            print form.errors
    else:
        form = CategoryForm()

    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list, 'form': form}
    return render(request, 'rango/add_category.html', context_dict)


def add_page(request, category_name_url):
    cat_list = get_category_list()
    category_name = decode_url(category_name_url)

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render(request, 'rango/add_page.html', {})

            page.views = 0
            page.save()

            return redirect("rango:category", category_name_url=category_name_url)
        else:
            print form.errors

    else:
        form = PageForm()

    return render(request, "rango/add_page.html", {'category_name_url': category_name_url,
                                              'category_name': category_name,
                                              'form': form,
                                              'cat_list': cat_list})


def register(request):
    cat_list = get_category_list()
    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            registered = True

        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, "rango/register.html", {
        'user_form': user_form,
        'profile_form': profile_form,
        'registered': registered,
        'cat_list': cat_list
    })


def user_login(request):
    cat_list = get_category_list()
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('rango:index')
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html', {'cat_list': cat_list})


def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)
            print result_list

    return render(request, 'rango/search.html', {'result_list': result_list})


@login_required
def profile(request):
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}
    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)

    except:
        up = None

    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render(request, 'rango/profile.html', context_dict)


@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")


@login_required
def user_logout(request):
    logout(request)
    return redirect("rango:index")


def track_url(request):
    page_id = None
    url = "{% url 'rango:index' %}"

    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views += 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)


def about(request):
    cat_list = get_category_list()
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0
    return render(request, 'rango/about.html', {'visits': count, 'cat_list': cat_list})




## Ajax Views
@login_required
def like_category(request):
    cat_id=None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    dict = {'likes': 0, 'user': 'zach'}
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            dict['likes'] += likes
            category.save()

    return HttpResponse(json.dumps(dict))


def suggest_category(request):
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/category_list.html', {'cat_list': cat_list })


@login_required
def auto_add_page(request):
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']

        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            if category:
                if url and title:
                    p = Page.objects.get_or_create(category=category, title=title, url=url)
                pages = Page.objects.filter(category=category).order_by('-views')
                context_dict['pages'] = pages

    return render(request, 'rango/page_list.html', context_dict)





