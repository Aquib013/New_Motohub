from django.contrib import messages
from django.db.models import Sum, F, Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from svc.models import Item
from svc.forms import ItemForm


class ItemListView(ListView):
    model = Item
    template_name = 'items/item_list.html'
    context_object_name = "items"
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(item_name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculate the total inventory value
        total_inventory_value = Item.objects.aggregate(
            total_inventory_value=Sum(F('item_quantity_in_stock') * F('cost_price'))
        )['total_inventory_value'] or 0
        # Add the total_inventory_value to the context
        context['total_inventory_value'] = total_inventory_value
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('items/partial_item_list.html', context, self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class ItemCreateView(CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('item-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_media'] = self.form_class().media
        return context

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
