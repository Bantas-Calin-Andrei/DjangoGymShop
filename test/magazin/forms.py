from django import forms
from .models import Product, Category
import json
import time
from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Promotion
from django.contrib.auth.forms import AuthenticationForm

#Lab5 Task1
class ProductFilterForm(forms.Form): 
    name = forms.CharField(required=False, label='Product Name', widget=forms.TextInput(attrs={'placeholder': 'Search by name'}))
    min_price = forms.DecimalField(required=False, min_value=0, label='Minimum Price')
    max_price = forms.DecimalField(required=False, min_value=0, label='Maximum Price')
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, label='Category')

#L5 Task 2
class ContactForm(forms.Form):
    name = forms.CharField(required=True, max_length=10, label="Nume")
    first_name = forms.CharField(required=False, label="Prenume")
    birth_date = forms.DateField(required=False, label="Data nașterii")
    email = forms.EmailField(required=True, label="E-mail")
    confirm_email = forms.EmailField(required=True, label="Confirmare e-mail")
    message_type = forms.ChoiceField(choices=[('reclamatie', 'Reclamație'), ('intrebare', 'Întrebare'),
                                              ('review', 'Review'), ('cerere', 'Cerere'), ('programare', 'Programare')],
                                     label="Tip mesaj")
    subject = forms.CharField(required=True, label="Subiect")
    min_days = forms.IntegerField(min_value=1, label="Minim zile așteptare")
    message = forms.CharField(widget=forms.Textarea, required=True, label="Mesaj")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        birth_date = cleaned_data.get("birth_date")
        message = cleaned_data.get("message")
        name = cleaned_data.get("name")

        # Valideaza email
        if email != confirm_email:
            self.add_error('confirm_email', "E-mailurile nu coincid.")

        # Valideaza varsta
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                self.add_error('birth_date', "Trebuie să fiți major pentru a trimite mesajul.")

        # Valideaza cate cuvinte sunt
        words = len([w for w in message.split() if w.isalnum()])
        if not (5 <= words <= 100):
            self.add_error('message', "Mesajul trebuie să conțină între 5 și 100 de cuvinte.")

        # Valideaza fara linkuri
        if any(word.startswith(('http://', 'https://')) for word in message.split()):
            self.add_error('message', "Mesajul nu poate conține linkuri.")

        # Valideaza daca mesajul se termina cu numele
        if name and not message.endswith(name):
            self.add_error('message', "Mesajul trebuie să fie semnat cu numele dvs.")
            
#L5 T3
class ProductForm(forms.ModelForm):
    stock = forms.IntegerField(label="Stock", required=True, min_value=0)
    price = forms.DecimalField(label="Price", required=True, min_value=0)

    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'image']
        help_texts = {
            'name': 'Enter the product name.',
            'description': 'Detailed description of the product.',
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class CustomUserRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(required=True, label="Număr de telefon")
    address = forms.CharField(widget=forms.Textarea, required=True, label="Adresă")
    date_of_birth = forms.DateField(required=True, label="Data nașterii")
    profile_picture = forms.ImageField(required=False, label="Poză de profil")
    bio = forms.CharField(widget=forms.Textarea, required=False, label="Descriere")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'bio', 'password1', 'password2']

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise forms.ValidationError("Numărul de telefon trebuie să conțină doar cifre.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob.year > 2005:
            raise forms.ValidationError("Trebuie să aveți cel puțin 18 ani pentru a vă înregistra.")
        return dob
    
    
class CustomLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, label="Ține-mă minte")

    def clean(self):
        cleaned_data = super().clean()
        # Aici poți adăuga validări suplimentare, dacă este cazul
        return cleaned_data
    

class PromotionForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Categories"
    )

    class Meta:
        model = Promotion
        fields = ['name', 'description', 'discount_percentage', 'categories', 'expires_at']
        labels = {
            'name': 'Promotion Name',
            'description': 'Description',
            'discount_percentage': 'Discount (%)',
            'expires_at': 'Expiration Date',
        }
