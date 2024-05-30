from django.shortcuts import render,reverse,redirect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages as mssg
from products.models import cake_list,orders,messages
from .forms import SignUpForm
from products.forms import make_order_form,message_form
import pandas as pd   
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


# Create your views here.

def indexpage(request):
    context = dict()
    context['title'] = 'indexpage'
    return render(request,'accounts/index.html',context)

def homepage(request):
    context = dict()
    items = cake_list.objects.all()
    context['items'] = items
    return render(request,'accounts/homepage.html',context)

def category_filter(request,category_name):
    context = dict()
    items = cake_list.objects.filter(category = category_name)
    context['items'] = items
    return render(request,'accounts/homepage.html',context)

def sign_up(request):
    form = SignUpForm(request.POST or None)
    context= dict()
    context["form"] = form
    if request.method == "POST":
        if form.is_valid(): 
            user=form.save()
            login(request,user)      
            return redirect(reverse('accounts:homepage'))
        else:
            mssg.info(request,form.errors)
            return render(request,'accounts/sign_up.html',context)
    return render(request,'accounts/sign_up.html',context)

def log_in(request):
    form = AuthenticationForm(request, data=request.POST)
    context= dict()
    context["form"] = form
    if request.method == "POST":
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username = username,password=password)
            login(request,user)  
            if user.is_superuser:
                return redirect(reverse('admin:dashboard'))
            if user:    
                return redirect(reverse('accounts:homepage'))
        else:
            return render(request,'accounts/log_in.html',context)    
    return render(request,'accounts/log_in.html',context)

def log_out(request):
    logout(request)
    return redirect(reverse('accounts:log-in'))

def my_orders(request):
    context = dict()
    user = request.user
    myorders = orders.objects.filter(user_id = user.id).order_by('-date')
    context['orders'] = myorders
    return render(request,'accounts/my_orders.html',context)

def cancel_order(request,id):
    order = orders.objects.get(id = id)
    order.order_status = 'Cancelled'
    order.save()
    mssg.info(request,'Order cancelled successfully. Refund will be credited to your bank account within 3-4 working days')
    return redirect(reverse('accounts:my-orders'))

def prediction(request):
    return render(request, 'accounts/prediction.html')

def analyze(request):
    crop = pd.read_csv("dataset/Crop_recommendation.csv")

    # remove duplicate values
    crop.drop_duplicates()

    # handle null values in dataset
    attr=["N","P","K","temperature","humidity","rainfall","label"]
    if crop.isna().any().sum() !=0:
        for i in range(len(attr)):
            crop[atrr[i]].fillna(0.0, inplace = True)

    #Remove unwanted parts from strings in a column 
    crop.columns = crop.columns.str.replace(' ', '') 

    # we have given 7 features to the algorithm
    features = crop[['N', 'P','K','temperature', 'humidity', 'ph', 'rainfall']]

    # dependent variable is crop
    target = crop['label']

    # our model will contain training and testing data
    x_train, x_test, y_train, y_test = train_test_split(features,target,test_size = 0.2,random_state =2)
    
    # here n_estimators is The number of trees in the forest.
    # random_state is for controlling  the randomness of the bootstrapping
    RF = RandomForestClassifier(n_estimators=20, random_state=0)

    # we'll use rf.fit to build a forest of trees from the training set (X, y).
    RF.fit(x_train,y_train)
    # at this stage our algorithm is trained and ready to use
    
    # take values from user
    N = request.POST.get('nitrogen', 'default')
    P = request.POST.get('phosphorous', 'default')
    K = request.POST.get('potassium', 'default')
    temp = request.POST.get('temperature', 'default')
    humidity = request.POST.get('humidity', 'default')
    ph =request.POST.get('ph', 'default')
    rainfall = request.POST.get('rainfall', 'default')

    # make a list of user input
    userInput = [N, P, K, temp, humidity, ph, rainfall]
    
    # use trained model to predict the data based on user input
    result = RF.predict([userInput])[0]

    # display  result to the user
    params = {'purpose':'Predicted Crop: ', 'analyzed_text': result.upper()}
    return render(request, 'accounts/analyze.html', params)    
    

def messages(request):
    context = dict()
    form = message_form(request.POST or None)
    context['form'] = form
    if request.method == "POST":
        if form.is_valid: 
            order=form.save()
            mssg.info(request,'Thank you for filling the form. Will get back to you soon')
    return render(request,'accounts/messages.html',context)

def checkout(request,id):
    context = dict()
    customer=request.user
    form = make_order_form(request.POST or None)
    context['customer'] = customer
    context['form'] = form
    if request.method == "POST":
        if form.is_valid: 
            order=form.save(commit = False)    
            order.user_id = customer.id
            order.cake_list_id = id
            order = order.save()
            context['id'] = id
            return render(request,'accounts/landingpage.html',context)
    return render(request,'accounts/delivery_details.html',context)

def landing_page(request):
    return render(request,'accounts/landingpage.html')

def payment_cancelled(request):
    cancel_order = orders.objects.latest('id')
    if cancel_order.status == 'Pending':
        cancel_order.delete()
    return redirect(reverse('accounts:homepage'))

def payment_successfull(request):
    success_order = orders.objects.latest('id')
    success_order.status = 'Success'
    success_order.save()
    return redirect(reverse('accounts:my-orders'))