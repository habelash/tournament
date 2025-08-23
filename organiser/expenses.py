
from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'description', 'receipt']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
