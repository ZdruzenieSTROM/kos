from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm #add this

from .models import Submission, User, Competitor, Grade, Game, Level, Problem
from .forms import RegisterForm, AnswerForm


def say_hello(request):
    return render(request, 'base.html')

def users_list(request):
    users = User.objects.filter(first_name='a2')
    return render(request, 'user_list.html', {'users': users})

def sutaz(request):
    from datetime import datetime, timezone
    
    level = None
   
    user = None
    if request.user.is_authenticated:
        user = request.user
        competitor = Competitor.objects.select_related().filter(user= user)[0]
    else:
        error_message = 'Neprihlaseny user.'
        return render(request, 'message.html', {'error_message' : error_message})

    if user is None or competitor is None:
        error_message = 'No user'
        return render(request, 'message.html', {'error_message' : error_message})

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AnswerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            level = Level.objects.get(pk=form.cleaned_data['level'])
            odpoved = form.cleaned_data['Odpoved']
            # vyhodnotenie otazky
            #PROBLEM
            problems = Problem.objects.filter(level= level)
            if len(problems) == 0:
                error_message = 'Nenasla sa uloha.'
                return render(request, 'message.html', {'error_message' : error_message})
            problem = problems[0]

            if odpoved != problem.solution:        
                error_message = 'Nespravna odpoved.'
            else:
                submition = Submission(problem = problem, competitor = competitor, competitor_answer = odpoved, submited_at = datetime.now(), correct = True)
                submition.save()
                levels = Level.objects.filter(previous_level = level)
                if len(levels) == 0:
                    error_message = "uspesne si ukoncil sutaz"
                    return render(request, 'message.html', {'error_message' : error_message})
                level = levels[0]




    # ziskam Game
    start_time = datetime.now(timezone.utc)
    games = Game.objects.filter(start__lt= start_time).filter(end__gt= start_time)
    if len(games) == 0:
        error_message = 'Momentálne pre teba nebeží súťaž.'
        return render(request, 'message.html', {'error_message' : error_message})
    game = games[0]

    #overime, ci este mame cas
    """
    if game.end < start_time:
        error_message = 'Tvoj čas uplynul, momentálne pre teba nebeží súťaž.'
        return render(request, 'message.html', {'error_message' : error_message})
    """

    diff = game.end - start_time
    error_message = None

    # LEVEL
    if level is None:
        levels = Level.objects.filter(game= game).filter(is_starting_level_for_grades= competitor.grade)
        if len(levels) == 0:
            error_message = 'Nenasiel sa ziaden level pre tvoj grade ' + competitor.grade
            return render(request, 'message.html', {'error_message' : error_message})
        else:
            level = levels[0]

    #PROBLEM
    problems = Problem.objects.filter(level= level)
    if len(problems) == 0:
        error_message = 'Nenasla sa uloha.'
        return render(request, 'message.html', {'error_message' : error_message})
    problem = problems[0]

    form = AnswerForm(initial={"level":level.pk})
    return render(request, 'sutaz.html', {'user':user, 'cas' : diff, 'error_message' : error_message, 'zadanie': problem,'form':form,'level':level})



def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return HttpResponseRedirect('/strom/main')
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form":form})
    

def user_register(request):
    # if this is a POST request we need to process the form data
    template = 'register.html'
   
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Username already exists.'
                })
            elif User.objects.filter(email=form.cleaned_data['email']).exists():
                return render(request, template, {
                    'form': form,
                    'error_message': 'Email already exists.'
                })
            elif form.cleaned_data['password'] != form.cleaned_data['password_repeat']:
                return render(request, template, {
                    'form': form,
                    'error_message': 'Passwords do not match.'
                })
            else:
                # Create the user:
                user = User.objects.create_user(
                    form.cleaned_data['username'],
                    form.cleaned_data['email'],
                    form.cleaned_data['password']
                )
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
                competitor = Competitor(user= user, school= form.cleaned_data['school'], is_active= True, grade=form.cleaned_data['grade'])
                competitor.save()
               
                # Login the user
                login(request, user)

                messages.success(request, "Registration successful." )
                
                # redirect to start the competition
                return HttpResponseRedirect('/strom/main')
                

   # No post data availabe, let's just show the page.
    else:
        form = RegisterForm()

    return render(request, template, {'form': form})    

def logout_request(request):
	logout(request)
	return HttpResponseRedirect('/strom/main')