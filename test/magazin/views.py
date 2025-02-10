from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from datetime import date
import json
import os
import time
from .models import Product, Category, View, Promotion, CustomUser
from .forms import ProductFilterForm, ContactForm, ProductForm, CustomUserRegistrationForm, CustomLoginForm, PromotionForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.mail import send_mail, send_mass_mail, mail_admins
from django.conf import settings
import uuid
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib import messages
import logging


def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

def home(request):
    return render(request, 'home.html')


def is_admin(user):
    return user.is_staff  


def product_list(request):
    # Preia toate produsele și adaugă o annotare pentru numărul de vizualizări
    products = Product.objects.annotate(view_count=Count('view'))

    # Filtrare pe baza parametrilor din request
    name_filter = request.GET.get('name', '')
    if name_filter:
        products = products.filter(name__icontains=name_filter)

    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category__name__icontains=category_filter)

    price_min = request.GET.get('price_min', '')
    if price_min:
        products = products.filter(price__gte=price_min)

    price_max = request.GET.get('price_max', '')
    if price_max:
        products = products.filter(price__lte=price_max)

    stock_filter = request.GET.get('stock', '')
    if stock_filter:
        products = products.filter(stock__gte=stock_filter)
    #Lab4 Task2
    # Paginare (10 produse per pagină)
    paginator = Paginator(products, 10)  # Schimbă la 5 pentru pagini mai mici
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product_list.html', {'page_obj': page_obj, 'products': page_obj.object_list})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # extrage datele din formular
            data = form.cleaned_data
            birth_date = data.pop('birth_date', None)
            data['age'] = None

            # Calculează vârsta dacă data de naștere este disponibilă
            if birth_date:
                today = date.today()
                age_years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                age_months = today.month - birth_date.month + 12 * ((today.month, today.day) < (birth_date.month, birth_date.day))
                data['age'] = f"{age_years} years and {age_months} months"

            # Elimină confirm_email din datele salvate
            data.pop('confirm_email', None)

            # Normalizează mesajul
            data['message'] = ' '.join(data['message'].replace('\n', ' ').split())

            # salvează datele într-un fișier JSON
            os.makedirs('mesaje', exist_ok=True)
            filename = f"mesaje/mesaj_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(data, f)

            return render(request, 'success.html', {'form': form})
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})



def add_product(request):
    
    if not request.user.has_perm('magazin.add_product'):
        raise PermissionDenied("Nu ai voie să adaugi produse.")

    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.stock = form.cleaned_data.get('stock')  # Mapează `stock`
            product.price = form.cleaned_data.get('price')  # Mapează `price`
            product.save()
            messages.success(request, 'Produsul a fost adăugat cu succes!')
            return render(request, 'add_product.html', {'form': form})
        else:
            messages.error(request, 'Eroare la salvarea produsului. Verifică datele introduse.')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})



def register(request):
    logger.debug('Începerea procesului de înregistrare a utilizatorului.')
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Verificare pentru username-ul "admin"
            if username.lower() == 'admin':
                # Trimite email către administratori
                subject = "Cineva încearcă să ne preia site-ul"
                message_text = f"Un utilizator a încercat să se înregistreze cu username-ul 'admin'.\nEmail: {email}"
                message_html = f"""
                    <h1 style="color: red;">Cineva încearcă să ne preia site-ul</h1>
                    <p>Un utilizator a încercat să se înregistreze cu username-ul 'admin'.</p>
                    <p><strong>Email:</strong> {email}</p>
                """
                mail_admins(subject, message_text, html_message=message_html)

                # Adaugă eroare formularului
                form.add_error('username', 'Acest username nu este permis.')
                return render(request, 'register.html', {'form': form})

            # Creare utilizator dacă username-ul este valid
            user = form.save(commit=False)
            user.cod = str(uuid.uuid4())  # Generare cod unic
            user.save()

            # Trimite e-mail de confirmare
            subject = "Confirmare e-mail"
            message = f"""
                Bun venit pe site, {user.first_name} {user.last_name}!
                Username-ul tău este: {user.username}.
                Te rugăm să confirmi e-mailul accesând linkul de mai jos:
                http://localhost:8000/magazin/confirma_mail/{user.cod}
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return redirect('login')  # Redirect la login după înregistrare
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'register.html', {'form': form})



def user_logout(request):
    logout(request)
    return redirect('home')


def confirma_mail(request, cod):
    try:
        user = CustomUser.objects.get(cod=cod)
        user.email_confirmat = True
        user.cod = None  # Resetează codul după confirmare
        user.save()
        return render(request, 'email_confirmed.html', {'user': user})
    except CustomUser.DoesNotExist:
        return render(request, 'email_not_confirmed.html')


logger = logging.getLogger(__name__)

def user_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.email_confirmat:
                form.add_error(None, "Trebuie să confirmi e-mailul înainte de a te autentifica.")
                return render(request, 'login.html', {'form': form})
            
            if user.blocat:
                messages.error(request, "Contul tău a fost blocat. Contactează un administrator.")
                return render(request, 'login.html', {'form': form})

            
            logout(request)
            login(request, user)
            
            remember_me = form.cleaned_data.get('remember_me')
            
            if remember_me:
                request.session.set_expiry(86400)  # 1 zi
            else:
                request.session.set_expiry(0)  # Închidere sesiune la logout  
                
            
                
            next_url = request.POST.get('next', 'profile')  # Default la 'profile'
            return redirect(next_url) 
        else:
            messages.error(request, "Numele de utilizator sau parola sunt incorecte. Te rugăm să încerci din nou.")
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})

#L6 T2
def register_view(request, product_id):
    if request.user.is_authenticated:
        product = Product.objects.get(id=product_id)
        # Adaugă vizualizarea
        View.objects.create(user=request.user, product=product)

        # Păstrează doar ultimele N vizualizări
        N = 5  # Numărul maxim de vizualizări
        user_views = View.objects.filter(user=request.user).order_by('-viewed_at')
        if user_views.count() > N:
            # Șterge cele mai vechi vizualizări
            for view in user_views[N:]:
                view.delete()

    return redirect('product_detail', product_id=product_id)




def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_views = View.objects.filter(product=product).count()

    # Realizează înregistrarea vizualizării
    if request.user.is_authenticated:
        View.objects.create(user=request.user, product=product)

    return render(request, 'product_detail.html', {'product': product, 'product_views': product_views})

def critical_view(request):
    try:
        # Cod care va genera o eroare de fișier
        with open('nonexistent_file.txt', 'r') as file:
            content = file.read()
    except Exception as e:
        subject = "Eroare Critică în Aplicație"
        message_text = f"Eroare: {str(e)}"
        message_html = f"""
        <h1 style="background-color: red; color: white;">Eroare Critică</h1>
        <p>{str(e)}</p>
        """
        mail_admins(subject, message_text, html_message=message_html)
        return render(request, 'error.html', {'error': str(e)})

    return render(request, 'success.html')

def some_view(request):
    if not request.user.is_authenticated:
        titlu = "Eroare acces resursă"
        mesaj_personalizat = "Nu ai permisiunea de a accesa această pagină."
        context = {
            'titlu': titlu,
            'mesaj_personalizat': mesaj_personalizat,
            'user': request.user,
        }
        html = render_to_string('403.html', context)
        return HttpResponseForbidden(html)
    return render(request, 'pagina_normala.html')

@login_required
def activate_offer(request):
    # Atribuie permisiunea `vizualizeaza_oferta` utilizatorului
    permission = Permission.objects.get(codename='vizualizeaza_oferta')
    request.user.user_permissions.add(permission)

    # Redirecționează către pagina de ofertă
    return redirect('offer_page')


@login_required
def profile(request):
    user_data = {
        'username': request.user.username,
        'email': request.user.email,
        'phone_number': request.user.phone_number,
        'address': request.user.address,
        'date_of_birth': request.user.date_of_birth,
        'bio': request.user.bio,
    }
    return render(request, 'profile.html', {'user_data': user_data})

# Schimbare Parolă
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

@permission_required('magazin.can_access_resource', raise_exception=True)
def restricted_view(request):
    # Cod pentru resursa protejată
    return render(request, 'restricted_page.html')

@login_required  
def create_promotion(request):
     # Verifică dacă utilizatorul este admin
    if not request.user.is_staff:  # Sau request.user.is_superuser pentru superuseri
        raise PermissionDenied  # Returnează eroarea 403 dacă nu este admin
    
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promotion = form.save()

            # Trimite e-mailuri utilizatorilor
            K = 3  # Număr minim de vizualizări pentru eligibilitate
            messages = []
            for category in promotion.categories.all():
                users = (
                    CustomUser.objects
                    .filter(view__product__category=category)
                    .annotate(view_count=models.Count('view'))
                    .filter(view_count__gte=K)
                    .distinct()
                )
                for user in users:
                    subject = f"Special Promotion: {promotion.name}"
                    message = f"""
                        Dear {user.username},

                        We have a special promotion for products in the {category.name} category!
                        - Discount: {promotion.discount_percentage}%
                        - Expires: {promotion.expires_at}

                        Don't miss out!
                    """
                    messages.append((subject, message, settings.DEFAULT_FROM_EMAIL, [user.email]))

            send_mass_mail(messages, fail_silently=False)
            return redirect('promotions')
    else:
        form = PromotionForm()

    return render(request, 'create_promotion.html', {'form': form})



def offer_page(request):
    if not request.user.has_perm('magazin.vizualizeaza_oferta'):
        return HttpResponseForbidden(render(request, '403.html', {
            'titlu': "Eroare afișare ofertă",
            'mesaj_personalizat': "Nu ai voie să vizualizezi oferta."
        }))
    return render(request, 'offer.html')
