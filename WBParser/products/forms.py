# products/forms.py

from django import forms

class ArticleForm(forms.Form):
    article = forms.CharField(
        label='',
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите артикул товара здесь',
            'class': 'search-input',  # Класс для оформления через CSS
        })
    )
