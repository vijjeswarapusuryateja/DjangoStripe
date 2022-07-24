from django.shortcuts import render, redirect # add redirect here
from .forms import NewUserForm
from django.contrib import messages

#import these
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm

import stripe
import djstripe
from djstripe.models import Product, Price
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

import json
from django.http import JsonResponse

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


# Create your views here.
def home(request):
    return render(request = request, template_name="main/home.html" )

def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful." )
            return redirect("main:home")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm
    return render (request=request, template_name="main/register.html", context={"form":form})

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
                return redirect("main:home")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="main/login.html", context={"form":form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    return redirect("main:home")


@method_decorator(login_required, name='dispatch')
class CheckoutView(TemplateView):
    template_name = "main/checkout.html"

    def get_context_data(self, **kwargs):
        products = Product.objects.all()
        context = super(CheckoutView, self).get_context_data(**kwargs)
        context.update({
            "products": products,
            "STRIPE_PUBLIC_KEY": settings.STRIPE_TEST_PUBLIC_KEY
        })
        return context



@method_decorator(login_required, name='dispatch')
class StripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:

            data = json.loads(request.body)
            print(data)
            payment_method = data['payment_method']

            payment_method_obj = stripe.PaymentMethod.retrieve(payment_method)
            djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method_obj)

        # This creates a new Customer and attaches the PaymentMethod in one API call.
            customer = stripe.Customer.create(
                payment_method=payment_method,
                email=request.user.email,
                invoice_settings={
                    'default_payment_method': payment_method
                }
              )

            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            request.user.customer = djstripe_customer
         

          # At this point, associate the ID of the Customer object with your
          # own internal representation of a customer, if you have one.
          # print(customer)

          # Subscribe the user to the subscription created
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                      "price": data["price_id"],
                    },
                ],
                expand=["latest_invoice.payment_intent"]
              )

            djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(subscription)

            request.user.subscription = djstripe_subscription
            request.user.customer = djstripe_customer
            request.user.save()

          
            # creating the intent
            price = Price.objects.get(id=self.kwargs["pk"])
            intent = stripe.PaymentIntent.create(
                amount=price.unit_amount,
                currency='usd',
                customer=customer['id'],
                description="Software development services",
                metadata={
                    "price_id": price.id
                }
            )
        


            return JsonResponse({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})


@login_required
def profile(request):
    if request.user.is_authenticated:
        if request.user.subscription:
            return render(request = request, template_name="main/profile.html" )
        else:
            return redirect("main:checkout")
    else:
        return redirect("main:register")




def cancel(request):
  if request.user.is_authenticated:
    sub_id = request.user.subscription.id

    try:
      stripe.Subscription.delete(sub_id)
    except Exception as e:
      return JsonResponse({'error': (e.args[0])}, status =403)


  return redirect("main:home")



@login_required
def product(request):
    if request.user.is_authenticated:
        if request.user.subscription:
            return render(request = request, template_name="main/product.html" )
        else:
            return redirect("main:checkout")
    else:
        return redirect("main:register")

