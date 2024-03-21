from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages

from dashboard.models import ContactMessage

def dashboard(request):
    page_title = 'Simtrail - A revolutionary flight tracker for virtual pilots.'
    context = {
        'page_title': page_title,
    }
    return render(request, 'dashboard/dashboard.html', context)

def roadmap(request):
    page_title = 'Roadmap - Simtrail'
    context = {
        'page_title': page_title,
    }
    return render(request, 'dashboard/roadmap.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        ContactMessage.objects.create(name=name, email=email, message=message)

        # Redirect to a new URL or show a success message
        return redirect('dashboard/dashboard.html')  # Replace 'success_url' with the name of the URL you'd like to redirect to
    else:
        # If not POST, render the form again or redirect as needed
        return render(request, 'dashboard/dashboard.html')

@login_required
def update_flight_hours_view(request):
    if request.method == 'POST':
        try:
            new_hours = int(request.POST.get('hours', 0))  # Default to 0 if not provided
            request.user.hours = new_hours
            request.user.save()
            # Redirect to a success page or back to the form with a success message
            return HttpResponseRedirect(reverse('dashboard'))
        except ValueError:
            # Return an error response or render the form again with an error message
            return render(request, 'update_hours.html', {
                'error_message': 'Invalid input. Please enter a valid number of flight hours.',
            })
    elif request.method == 'GET':
        # Render the form for GET requests
        return render(request, 'dashboard/update_hours.html')
    else:
        # Optionally handle other methods, such as PUT, DELETE, etc., if needed
        return HttpResponse("Method not allowed.", status=405)




@login_required
def make_user_staff(request, user_id):
    User = get_user_model()  # Get the active user model
    try:
        user = User.objects.get(id=user_id)
        user.is_staff = True
        user.save()
        return HttpResponse("User is now staff.")
    except User.DoesNotExist:
        return HttpResponse("User not found.", status=404)

@login_required
def update_user_flight_hours(request, user_id, new_hours):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to update flight hours for other users.")
        return redirect('dashboard')

    try:
        User = get_user_model()  # Get the active user model
        user = User.objects.get(id=user_id)

        # Since new_hours is now directly passed as a parameter, just convert it to an integer
        if str(new_hours).isdigit(): 
            user.hours = int(new_hours)
            user.save()
            messages.success(request, f"Flight hours updated successfully for {user.username}.")
        else:
            messages.error(request, "Invalid input. Please enter a valid number of flight hours.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")

    return redirect('dashboard')
