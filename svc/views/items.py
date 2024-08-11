from django.contrib import messages
from django.db.models import Sum, F
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from svc.models import Item
from svc.forms import ItemForm


class ItemListView(ListView):
    model = Item
    template_name = 'items/item_list.html'
    context_object_name = "items"
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate the total inventory value
        total_inventory_value = Item.objects.aggregate(
            total_inventory_value=Sum(F('item_quantity_in_stock') * F('cost_price'))
        )['total_inventory_value'] or 0
        # Add the total_inventory_value to the context
        context['total_inventory_value'] = total_inventory_value
        return context


class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('item-list')

    def form_valid(self, form):
        item = form.save(commit=False)
        item.save()
        messages.success(self.request, "Item Added successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            if field == '__all__':
                for error in errors:
                    messages.error(self.request, f"Error: {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


class ItemDetailView(DetailView):
    model = Item
    template_name = 'items/item_detail.html'


class ItemUpdateView(UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('item-list')


class ItemDeleteView(DeleteView):
    model = Item
    template_name = 'items/item_confirm_delete.html'
    success_url = reverse_lazy('item-list')
