from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin

from core.form import RentalForm
from .models import Item, Rental


@login_required
def rent_item(request, item_id: int) -> Any:
    item = get_object_or_404(Item, pk=item_id)
    rental = Rental(item=item, client=request.user)
    rental.save()

    item.available = False
    item.save()

    return redirect("items_list")


class ItemListView(generic.ListView):
    model = Item
    template_name = "items_list.html"
    context_object_name = "items"

    def get_queryset(self) -> QuerySet[Any]:
        return Item.objects.all().order_by("name")


class ItemCreateView(generic.CreateView):
    model = Item
    fields = ["name", "available"]
    template_name = "item_form.html"
    success_url = "/"


class RentalListView(generic.ListView):
    model = Rental
    template_name = "rental_list.html"
    context_object_name = "rentals"

    def get_queryset(self) -> QuerySet[Any]:
        return Rental.objects.all().order_by("date", "period", "period_time")


class RentalCreateView(LoginRequiredMixin, generic.CreateView):
    model = Rental
    form_class = RentalForm
    template_name = "rental_form.html"
    success_url = reverse_lazy("core:rental_list")

    def form_valid(self, form):
        item = form.cleaned_data.get("item")
        date = form.cleaned_data.get("date")
        period = form.cleaned_data.get("period")
        period_time = form.cleaned_data.get("period_time")

        existing_rental = Rental.objects.filter(
            item=item, date=date, period=period, period_time=period_time
        ).exists()

        if existing_rental:
            form.add_error(None, "This rental already exists.")
            return self.form_invalid(form)

        rental = form.save(commit=False)

        if self.request.user.is_superuser:
            rental.client = form.cleaned_data.get("client")
        else:
            rental.client = self.request.user
        rental.save()
        return super().form_valid(form)


class RentalDeleteView(generic.DeleteView):
    model = Rental
    template_name = "rental_confirm_delete.html"
    success_url = reverse_lazy("core:rental_list")


class RentalEditView(generic.UpdateView):
    model = Rental
    form_class = RentalForm
    template_name = "rental_form.html"
    success_url = reverse_lazy("core:rental_list")

    def form_valid(self, form):
        item = form.cleaned_data.get("item")
        date = form.cleaned_data.get("date")
        period = form.cleaned_data.get("period")
        period_time = form.cleaned_data.get("period_time")

        existing_rental = (
            Rental.objects.filter(
                item=item, date=date, period=period, period_time=period_time
            )
            .exclude(pk=self.object.pk)
            .exists()
        )

        if existing_rental:
            form.add_error(None, "Esse agendamento já existe.")
            return self.form_invalid(form)

        rental = form.save(commit=False)

        if self.request.user.is_superuser:
            rental.client = form.cleaned_data.get("client")
        else:
            rental.client = self.request.user
        rental.save()

        return super().form_valid(form)
