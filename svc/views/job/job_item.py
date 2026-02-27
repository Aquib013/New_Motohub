from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, CreateView, DeleteView
import json

from svc.forms import JobItemForm
from svc.models import JobItem, Job, Item


class JobItemEditView(UpdateView):
    model = JobItem
    form_class = JobItemForm
    template_name = 'job/job_item/add_item.html'
    context_object_name = 'job_item'

    def form_valid(self, form):
        job_item = form.save()
        messages.success(self.request, f"Item '{job_item.item}' successfully updated for Job #{job_item.job.job_no}")
        return redirect('job_detail', pk=job_item.job.pk)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            if field == '__all__':
                for error in errors:
                    messages.error(self.request, f"Error: {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job
        context['form_media'] = self.form_class().media
        return context


# ── API endpoints ──

def get_item_details(request):
    item_id = request.GET.get('id')
    try:
        item = Item.objects.get(id=item_id)
        return JsonResponse({
            'item_MRP': str(item.item_MRP),
            'cost_price': str(item.cost_price),
            'stock': item.item_quantity_in_stock,
        })
    except Item.DoesNotExist:  # NOQA
        return JsonResponse({'error': 'Item not found'}, status=404)


def search_items(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    items = Item.objects.filter(item_name__icontains=query)[:10]
    results = [{
        'id': item.id,
        'name': item.item_name,
        'mrp': str(item.item_MRP),
        'cost_price': str(item.cost_price),
        'stock': item.item_quantity_in_stock,
    } for item in items]
    return JsonResponse(results, safe=False)


@csrf_exempt
def add_job_item_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    try:
        data = json.loads(request.body)
        job = Job.objects.get(pk=pk)

        is_custom = data.get('is_custom', False)

        if is_custom:
            job_item = JobItem(
                job=job,
                custom_item_name=data['custom_item_name'],
                item_quantity=data['quantity'],
                item_unit_price=data['unit_price'],
                item_price=data['quantity'] * data['unit_price'],
            )
            job_item.save()
        else:
            item = Item.objects.get(id=data['item_id'])
            if data['quantity'] > item.item_quantity_in_stock:
                return JsonResponse({
                    'error': f'Only {item.item_quantity_in_stock} in stock'
                }, status=400)
            if data['unit_price'] < float(item.cost_price):
                return JsonResponse({
                    'error': f'Price must be above cost: ₹{item.cost_price}'
                }, status=400)

            job_item = JobItem(
                job=job,
                item=item,
                item_quantity=data['quantity'],
                item_unit_price=data['unit_price'],
                item_price=data['quantity'] * data['unit_price'],
            )
            job_item.save()

        job.refresh_from_db()

        return JsonResponse({
            'success': True,
            'job_item': {
                'id': job_item.id,
                'name': job_item.display_name,
                'quantity': job_item.item_quantity,
                'unit_price': str(job_item.item_unit_price),
                'total_price': str(job_item.item_price),
            },
            'job_total_item_cost': str(job.total_item_cost),
            'job_amount': str(job.job_amount),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def delete_job_item_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    try:
        job_item = JobItem.objects.get(pk=pk)
        job = job_item.job
        job_item.delete()
        job.refresh_from_db()
        return JsonResponse({
            'success': True,
            'job_total_item_cost': str(job.total_item_cost),
            'job_amount': str(job.job_amount),
        })
    except JobItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
